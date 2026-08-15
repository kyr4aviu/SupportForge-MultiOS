FROM alpine:3.23

RUN apk add --no-cache \
        font-dejavu \
        novnc \
        openbox \
        python3 \
        python3-tkinter \
        x11vnc \
        xvfb \
    && adduser -D -h /home/supportforge supportforge

WORKDIR /opt/supportforge

COPY --chown=supportforge:supportforge supportforge ./supportforge
COPY --chown=supportforge:supportforge tests ./tests
COPY --chown=supportforge:supportforge scripts ./scripts
COPY --chown=supportforge:supportforge README.md pyproject.toml ./
COPY --chown=supportforge:supportforge deployment/linux-gui-test/start-gui.sh /usr/local/bin/start-supportforge-gui

RUN chmod 755 /usr/local/bin/start-supportforge-gui \
    && python3 -m unittest discover -s tests -v

USER supportforge
ENV DISPLAY=:1 \
    HOME=/home/supportforge \
    PYTHONUNBUFFERED=1

EXPOSE 6080
CMD ["/usr/local/bin/start-supportforge-gui"]
