import pytest

from rhas_driver_qemu import driver
from rhas_driver_qemu.driver import Qemu


@pytest.fixture
def host(monkeypatch):
    """Fake an aarch64 host; tests set which binaries exist and whether /dev/kvm is usable."""
    state = {"kvm": False, "files": set(), "path": set()}

    monkeypatch.setattr(driver.platform, "machine", lambda: "aarch64")
    monkeypatch.setattr(
        driver.os, "access", lambda p, mode: state["kvm"] if p == "/dev/kvm" else False
    )
    monkeypatch.setattr(driver.Path, "exists", lambda self: str(self) in state["files"])
    monkeypatch.setattr(
        driver.shutil, "which", lambda name: f"/usr/bin/{name}" if name in state["path"] else None
    )
    return state


def select(**config):
    return Qemu(arch="aarch64", **config).children["power"]._select_qemu()


def test_bare_metal_uses_qemu_kvm_with_kvm(host):
    host["kvm"] = True
    host["files"] = {"/usr/libexec/qemu-kvm"}
    assert select() == ("/usr/libexec/qemu-kvm", "kvm")


def test_bare_metal_prefers_kvm_over_installed_qemu_system(host):
    host["kvm"] = True
    host["files"] = {"/usr/libexec/qemu-kvm"}
    host["path"] = {"qemu-system-aarch64"}
    assert select() == ("/usr/libexec/qemu-kvm", "kvm")


def test_bare_metal_without_known_qemu_kvm_path_keeps_bare_name(host):
    host["kvm"] = True
    assert select() == ("qemu-kvm", "kvm")


def test_no_kvm_prefers_qemu_system_when_installed(host):
    host["files"] = {"/usr/libexec/qemu-kvm"}
    host["path"] = {"qemu-system-aarch64"}
    assert select() == ("qemu-system-aarch64", None)


def test_no_kvm_falls_back_to_qemu_kvm_with_tcg(host):
    host["files"] = {"/usr/libexec/qemu-kvm"}
    assert select() == ("/usr/libexec/qemu-kvm", "tcg")


def test_foreign_arch_never_uses_qemu_kvm(host):
    host["kvm"] = True
    host["files"] = {"/usr/libexec/qemu-kvm"}
    host["path"] = {"qemu-system-x86_64"}
    assert Qemu(arch="x86_64").children["power"]._select_qemu() == ("qemu-system-x86_64", None)


def test_no_usable_qemu_raises_clear_error(host):
    with pytest.raises(RuntimeError, match="qemu-system-aarch64 is not installed"):
        select()


def test_sidecar_assumes_qemu_kvm_with_kvm(host, tmp_path):
    assert select(launcher_socket=str(tmp_path / "launcher.sock")) == ("/usr/libexec/qemu-kvm", "kvm")


@pytest.mark.parametrize(
    "arch, accel, expected",
    [
        ("aarch64", "kvm", "host"),
        ("aarch64", "tcg", "max,pauth-impdef=on"),
        ("aarch64", None, "max,pauth-impdef=on"),
        ("x86_64", "kvm", "host"),
        ("x86_64", None, "qemu64,+ssse3,+sse4.1,+sse4.2,+popcnt"),
    ],
)
def test_default_cpu(arch, accel, expected):
    assert Qemu(arch=arch).children["power"]._default_cpu(accel) == expected
