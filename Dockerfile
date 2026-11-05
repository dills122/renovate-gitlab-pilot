FROM renovate/renovate:44.216.2@sha256:435c302302f1db679e9b482f8dfd7e1e0c3b6938df44f9444780064c9a4d2c4f
USER root
ADD --checksum=sha256:a1cdd7b468386a9d78a081da05d6049d7e598db62a299db92df21a7062a4b183 https://registry.npmjs.org/pnpm/-/pnpm-10.23.0.tgz /tmp/lab-pnpm.tgz
RUN mkdir /opt/lab-pnpm \
    && tar -xzf /tmp/lab-pnpm.tgz --strip-components=1 -C /opt/lab-pnpm \
    && ln -s /opt/lab-pnpm/bin/pnpm.cjs /usr/local/bin/pnpm \
    && rm /tmp/lab-pnpm.tgz
USER 12021
