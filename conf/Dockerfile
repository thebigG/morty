#Run this from parent directory(root of the repo)
FROM ubuntu:18.04
RUN apt-get -qq update && \
    apt-get -q -y upgrade && \
    apt-get install -y sudo curl wget locales git vim screen libncurses5-dev pkg-config gawk wget git-core diffstat unzip texinfo gcc-multilib build-essential chrpath socat cpio python python3 python-pip libsdl1.2-dev sudo && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd lgomez --gid 1000
RUN useradd lgomez --uid 1000 --gid 1000
RUN mkdir /home/lgomez && chown lgomez:lgomez -R /home/lgomez
RUN mkdir /yocto && chown lgomez:lgomez -R /yocto

RUN locale-gen en_US.UTF-8

# Ensure that we always use UTF-8
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
COPY . /yocto
USER lgomez

WORKDIR /yocto
SHELL ["/bin/bash", "-c"]
RUN source oe-init-build-env
RUN  cp conf/* build/conf 
RUN cp conf/bblayers.conf.docker build/conf/bblayers.conf
RUN cp conf/local.conf.docker build/conf/local.conf
RUN  source oe-init-build-env && cd .. && make minimal-image



#RUN cd /yocto && git clone git://git.yoctoproject.org/poky
#RUN cd /yocto/poky && git checkout sumo
#RUN cd /yocto/poky/ && git clone -b sumo https://github.com/Xilinx/meta-xilinx.git
#SHELL ["/bin/bash", "-c"]
#RUN cd /yocto/poky && source oe-init-build-env && bitbake-layers add-layer "/yocto/poky/meta-xilinx/meta-xilinx-bsp"
#RUN cd /yocto/poky && echo "MACHINE ??= \"zedboard-zynq7\"" >> build/conf/local.conf

#RUN cd /yocto/poky && source oe-init-build-env && bitbake core-image-minimal

#ADD meta-dts /yocto/poky/meta-dts
#RUN sudo chown dinne:dinne -R /yocto/poky/meta-dts
#RUN cd /yocto/poky && source oe-init-build-env && bitbake-layers add-layer "/yocto/poky/meta-dts"
#need to remove repodata dir, otherwise we'll get a mv error (the target dir is not empty...)
#RUN rm -rf /yocto/poky/build/tmp/work/zedboard_zynq7-poky-linux-gnueabi/core-image-minimal/1.0-r0/oe-rootfs-repo/repodata && cd /yocto/poky && source oe-init-build-env && bitbake core-image-minimal 
