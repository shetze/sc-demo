# rhas-starter

A starter project for building RHIVOS/AutoSD images with a simple test application.

## TLDR

Build a C++ application, package it as an RPM, and install it into an AutoSD OS image using the Automotive Image Builder. Then boot the image as a QEMU virtual device via Jumpstarter and run automated tests to validate everything works.

## Description

This project demonstrates a complete build-test-validate workflow for automotive software targeting AutoSD/RHIVOS. It serves as a baseline you can fork and adapt for your own development.

- A simple C++ application (`auto-app`) is developed and built with CMake, either interactively in a DevSpaces workspace or as part of an automated pipeline.
- The application is packaged as an RPM using rpmbuild and included in an AutoSD OS image via an `.aib.yml` manifest.
- The OS image is flashed onto a QEMU-based virtual device managed by Jumpstarter, running on a bare-metal ARM node in the OpenShift cluster.
- Automated pytest tests boot the virtual device, log in over the serial console, and verify that the installed application runs correctly.

## Running the build and validation

There are two ways to build and validate:

- **Interactive development** in Red Hat OpenShift DevSpaces — build, test, and iterate on the application directly in a browser-based cloud workspace.
- **Automated pipeline** using OpenShift Pipelines with Pipelines-as-Code (PAC) — an end-to-end pipeline triggered automatically by pushes or pull requests to `main`.

### Interactive development

Open this repository in OpenShift DevSpaces to get a pre-configured workspace with all required tools (CMake, rpmbuild, `caib` CLI, Jumpstarter CLI).

1. Build the application: `make build-local`
2. Build the RPM: `make build-rpm-local`
3. Build the OS image using the `caib` CLI and the manifest at `manifests/auto-app.aib.yml`.
4. Flash and test the image on a Jumpstarter virtual device using `pytest tests/boot_test.py`.

See the Makefile for all available targets.

### Pipelines-as-Code

PipelineRun definitions live in the `.tekton/` directory. A GitHub webhook sends push and pull request events to the PAC controller on the OpenShift cluster. PAC matches the event against annotations in `.tekton/pr-build-validate.yaml` and triggers the pipeline when changes are made to `src/**` or `manifests/**` on the `main` branch.

The pipeline runs the following steps:

1. **clone-repo** — clone the source repository.
2. **build-rpm** — build the C++ application and package it as an RPM.
3. **build-os** — build an AutoSD qcow2 image with the RPM installed.
4. **flash** — flash the image onto a QEMU virtual device via a Jumpstarter lease.
5. **validate** — run `pytest tests/boot_test.py` to verify boot, login, and application execution.

To trigger a pipeline run, push a commit or open a pull request that modifies files under `src/` or `manifests/`.

## Setup

### OpenShift DevSpaces preparation

1. Register as a user in RHAS by signing up through Keycloak.
2. Log into the OpenShift web console and launch DevSpaces.
3. Configure DevSpaces preferences:
   - **Git config:** set your git username and email.
   - **Personal Access Token:** create a token named `git-pac` using a GitHub PAT with permissions to create webhooks and push/pull to the repository.
4. Create a new DevSpaces workspace from `https://github.com/rhadp-examples/rhas-starter`.

### OpenShift DevSpaces workspace setup

1. Get your OpenShift login token from the OpenShift web console: **Copy login command** > **Display Token** > copy the token.
2. Open a terminal in the workspace and paste the login command to complete OpenShift setup.
3. Log into Jumpstarter: run `jmp-login`, follow the Keycloak link, and authenticate.
4. Verify the setup: run `caib status` to confirm the Builder connection is working.

### Project / Pipeline-as-Code setup

Run `scripts/buildspace.sh <GITHUB_PAT>` to set up the pipeline infrastructure. The script:

- Creates a dedicated namespace for pipeline runs and assigns required RBAC roles to the pipeline service account.
- Creates configmaps with Jumpstarter and Builder operator endpoints.
- Registers a GitHub webhook pointing to the PAC controller on the cluster.
- Creates a PAC `Repository` custom resource linking the GitHub repo to the namespace.

## Stack

- **Red Hat OpenShift** — Kubernetes platform running the cluster, including bare-metal ARM nodes for virtual device testing.
- **Red Hat OpenShift DevSpaces** — browser-based cloud development environment (based on Eclipse Che) for interactive development.
- **Red Hat OpenShift Pipelines** — Tekton-based CI/CD pipelines with Pipelines-as-Code for GitHub-triggered automation.
- **Red Hat Automotive Suite (RHAS)** — platform providing the Jumpstarter and Builder operators on OpenShift for automotive software development.
- **AutoSD / RHIVOS** — CentOS Automotive Stream Distribution (upstream) and Red Hat In-Vehicle Operating System (downstream) for software-defined vehicles.
- **Automotive Image Builder (AIB)** — tool that assembles AutoSD/RHIVOS packages into deployable OS images from `.aib.yml` manifests.
- **Jumpstarter** — hardware-in-the-loop testing framework for booting and validating OS images on virtual or physical devices.
- **Red Hat build of Keycloak** — identity and access management for user authentication across the platform.
- **GitHub** — source code hosting and webhook integration to trigger pipeline runs via PAC.

test