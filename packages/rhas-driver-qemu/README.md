# RHAS QEMU Driver

`rhas-driver-qemu` is the RHAS fork of the [jumpstarter](https://jumpstarter.dev)
QEMU driver, adding TPM (`swtpm`) support, a `virtio` transport option
(`mmio`/`pci`), disk/memory resizing, and OCI-image flashing via
[`fls`](https://github.com/jumpstarter-dev/fls).

## Installation

```console
$ uv pip install "git+https://github.com/rhadp-examples/rhas-starter@main#subdirectory=packages/rhas-driver-qemu"
```

## Configuration

Example configuration:

```yaml
export:
  qemu:
    type: rhas_driver_qemu.driver.Qemu
    config:
      arch: aarch64
      smp: 2
      mem: 512M
      tpm: true
      virtio_transport: mmio
      default_partitions:
        root: /var/lib/jumpstarter/images/root.qcow2
```

## Acceleration

When `arch` matches the host and `/dev/kvm` is usable (bare metal), the driver
runs `qemu-kvm` with KVM. Without KVM it uses `qemu-system-<arch>` (TCG) if
installed; otherwise, for the host's own arch, it falls back to `qemu-kvm
-accel tcg`. This covers RHEL/CentOS images, which ship only `qemu-kvm`, on
nodes without nested virtualization. Without KVM the default aarch64 CPU is
`max,pauth-impdef=on`. TCG emulation is much slower than KVM, so
allow longer boot timeouts.

## Drivers

- `RhasQemu` (`rhas_driver_qemu.driver.Qemu`) — composite driver managing the
  QEMU virtual machine (power, console, VNC, and flasher children).
- `RhasQemuPower` (`rhas_driver_qemu.driver.QemuPower`) — starts/stops the QEMU
  process.
- `RhasQemuFlasher` (`rhas_driver_qemu.driver.QemuFlasher`) — flashes images to
  disk partitions, including OCI references (`oci://...`) via `fls`.

## Client API

```python
client.qemu.power.on()
client.qemu.power.off()
client.qemu.set_disk_size("20G")
client.qemu.set_memory_size("2G")
client.qemu.flash_oci("oci://registry.example.com/image:latest")

with client.qemu.novnc() as url:
    ...

with client.qemu.shell() as conn:
    ...
```
