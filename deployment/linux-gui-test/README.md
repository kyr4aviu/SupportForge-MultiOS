# Lightweight Linux GUI test

This image is an Alpine Linux GUI smoke-test environment for SupportForge
MultiOS. It uses Xvfb, Openbox, x11vnc, and noVNC instead of a full desktop
distribution.

## Build and run

From the repository root:

```sh
docker build -f deployment/linux-gui-test/Dockerfile -t supportforge-linux-gui:1.0.3 .
docker run --rm -d \
  --name supportforge-linux-gui \
  -p 127.0.0.1:6080:6080 \
  supportforge-linux-gui:1.0.3
```

Open:

```text
http://localhost:6080/vnc.html?autoconnect=1&resize=scale
```

Stop it with:

```sh
docker stop supportforge-linux-gui
```

## Test scope

This validates Alpine/musl compatibility, Python/Tk startup, widget layout,
exports, history, and container-visible diagnostics. It does not validate a
normal Linux host's systemd services, journal, hardware, storage, networking,
or Docker daemon. Perform final Linux validation in a real VM or machine.
