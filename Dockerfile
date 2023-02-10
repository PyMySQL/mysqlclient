FROM ubuntu:20.04
LABEL maintainer="support@tiledb.io"

ENV AWS_EC2_METADATA_DISABLED true

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=GMT

RUN apt-get update && apt-get install -y \
  gosu \
  pwgen \
  tzdata \
  gcc \
  g++ \
  build-essential \
  libasan5 \
  bison \
  chrpath \
  cmake \
  gdb \
  gnutls-dev \
  libaio-dev \
  libboost-dev \
  libdbd-mysql \
  libjudy-dev \
  libncurses5-dev \
  libpam0g-dev \
  libpcre3-dev \
  libreadline-gplv2-dev \
  libstemmer-dev \
  libssl-dev \
  libnuma-dev \
  libxml2-dev \
  lsb-release \
  perl \
  psmisc \
  zlib1g-dev \
  libcrack2-dev \
  cracklib-runtime \
  libjemalloc-dev \
  libsnappy-dev \
  liblzma-dev \
  libzmq3-dev \
  uuid-dev \
  ccache \
  git \
  wget \
  python3 \
  python3-dev \
  python3-pip \
  && rm -rf /var/lib/apt/lists/*

ENV MTR_MEM /tmp

WORKDIR /tmp

ENV TILEDB_VERSION="2.6.2"

# Install tiledb using 2.6 release
RUN mkdir build_deps && cd build_deps \
 && git clone https://github.com/TileDB-Inc/TileDB.git -b ${TILEDB_VERSION} && cd TileDB \
 && mkdir -p build && cd build \
 && cmake -DTILEDB_VERBOSE=OFF -DTILEDB_S3=ON -DTILEDB_SERIALIZATION=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr .. \
 && make -j$(nproc) \
 && make install-tiledb \
 && cd /tmp && rm -r build_deps

ENV MARIADB_VERSION="mariadb-10.5.13"

ARG MYTILE_VERSION="0.12.1"

# Download mytile release
RUN wget https://github.com/TileDB-Inc/TileDB-MariaDB/archive/${MYTILE_VERSION}.tar.gz -O /tmp/${MYTILE_VERSION}.tar.gz \
  && tar xf /tmp/${MYTILE_VERSION}.tar.gz \
  && mv TileDB-MariaDB-${MYTILE_VERSION} mytile

# Copy example arrays to opt
RUN cp -r /tmp/mytile/mysql-test/mytile/test_data/tiledb_arrays /opt/

# Install curl after building tiledb
RUN apt-get update && apt-get install -y \
  libcurl4 \
  libcurl4-openssl-dev \
  && rm -rf /var/lib/apt/lists/*

RUN wget https://downloads.mariadb.org/interstitial/${MARIADB_VERSION}/source/${MARIADB_VERSION}.tar.gz \
  && tar xf ${MARIADB_VERSION}.tar.gz \
  && mv /tmp/mytile ${MARIADB_VERSION}/storage/mytile \
  && cd ${MARIADB_VERSION} \
  && mkdir builddir \
  && cd builddir \
  && cmake -DPLUGIN_INNODB=NO \
        -DPLUGIN_TOKUDB=NO \
        -DPLUGIN_ROCKSDB=NO \
        -DPLUGIN_MROONGA=NO \
        -DPLUGIN_SPIDER=NO \
        -DPLUGIN_SPHINX=NO \
        -DPLUGIN_FEDERATED=NO \
        -DPLUGIN_FEDERATEDX=NO \
        -DPLUGIN_CONNECT=NO \
        -DPLUGIN_PERFSCHEMA=NO \
        -DCMAKE_BUILD_TYPE=Release \
        -SWITH_DEBUG=0 \
        -DWITH_EMBEDDED_SERVER=ON \
        -DCMAKE_INSTALL_PREFIX=/opt/server .. \
  && make -j$(nproc) \
  && make install \
  && cd ../../ \
  && rm -r ${MARIADB_VERSION}

# Add server binaries to path
ENV PATH="${PATH}:/opt/server/bin"

# Set ld library paths
RUN echo "/usr/local/lib" >> /etc/ld.so.conf.d/usr-local.conf
RUN echo "/usr/local/lib64" >> /etc/ld.so.conf.d/usr-local.conf
RUN echo "/opt/server/lib" >> /etc/ld.so.conf.d/usr-local.conf
RUN echo "/opt/server/lib64" >> /etc/ld.so.conf.d/usr-local.conf
RUN echo "/opt/server/lib/plugin" >> /etc/ld.so.conf.d/usr-local.conf
RUN echo "/opt/server/lib64/plugin" >> /etc/ld.so.conf.d/usr-local.conf

RUN ldconfig /usr/local/lib

ADD . /opt/tiledb-sql-py

WORKDIR /opt/tiledb-sql-py

# Newer setup tools needed for find_namespace_packages
RUN pip3 install --upgrade setuptools

RUN pip3 install -r requirements.txt

RUN pip3 install .

RUN pip3 install pandas numpy tiledb sqlalchemy

WORKDIR /opt/

CMD ["python3"]
