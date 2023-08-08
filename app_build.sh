[satshara@wsa299-client02 ~/work/main/coeus]$ cat release/app_build.sh
dth: 4 -*-
# $Header$
#
#
# This script will build the coeus applications (binaries).
#
set -x

# get source up to date
# Run co_helper to grab any bits needed.
(   cd $IPROOT || fail 1 'Failed to cd to $IPROOT'
    /usr/local/bin/python co_helper.py -v || fail 1 "Failed to run co_helper"
    touch third_party/NO_AUTO_PATH || fail 1 "Failed to touch NO_AUTO_PATH"
) || exit 1


PROX_ROOT=$IPROOT/coeus/prox
export PROX_ROOT
CVS_SERVER_NAME="engci-maven.cisco.com/artifactory/content-security-builds-group"
BUILD_DATE=`date +%Y-%m-%d`

# Directory to store the package (tarball) we are creating
PACKAGE_DIR=`pwd`/package
export PACKAGE_DIR

PYTHONPATH=
export PYTHONPATH

password_file="password_words.txt"

# figure out plat / rel
PLAT=`uname -p`
REL=`uname -r | cut -d- -f1`

fail() {
    # $1 = exit code
    # $2 = message to print (optional)
    if [ "x$2" != "x" ]
    then
        echo "ERROR: $2"
    fi
    exit $1
}

install_samba_conf_files() {
    # install samba configuration files
    echo ""
    echo "Copying samba configuration files..."

    KRB5_CONFDIR=$PACKAGE_DIR/etc
    SAMBA_CONFDIR=$PACKAGE_DIR/usr/local/etc
    WINBINDD_CONFDIR=$PACKAGE_DIR/etc
    install -o root -g wheel -m 0644 $PROX_ROOT/root_generic/etc/krb5.conf $KRB5_CONFDIR/ || fail 1 "Failed to copy krb5.conf"
    install -o root -g wheel -m 0644 $PROX_ROOT/root_generic/etc/samba/smb.conf $SAMBA_CONFDIR/ || fail 1 "Failed to copy smb.conf"
    install -o root -g wheel -m 0644 $PROX_ROOT/root_generic/etc/winbindd_template.conf $WINBINDD_CONFDIR/ || fail 1 "Failed to copy winbindd_template.conf"

}

#PACKAGE_RECURSIVE=package-recursive
PACKAGE_RECURSIVE=package
export PACKAGE_RECURSIVE

package_build() {
    echo "package_build (app_build.sh) $1 $2"
    package_path=$1
    here=`pwd`
    cd $package_path
    PKGNAME=`make -V PKGNAME`
    if pkg info -e $PKGNAME
    then
        echo "$1 aready installed"
    else
        # Now we know that package is not installed yet, so we go ahead and either build it from scratch
        # or install it from cs-packages.sgg.cisco.com
        echo "$package_path" | grep -q "^/usr/ports"
        if [ $? -eq 0 ] || ( [ ! -z $2 ] && [ "$2" == "package" ] )
        then
            # At this point we need try to install prebuilt package.  However, pkg_add for some reason returns 0 when
            # package dependencies are not found.  This is potentially problematic, so we need to make sure that all
            # dependencies are built and eventually copied to cvs.eng.sgg.cisco.com.  We refer to cvs.eng as cvs.ironport.com
            # as it resolves to different mirror depending on geographic location.
            #
            # We needed a way to check if pkg_add -r PKNAME will be able to observe dependencies, so to do that we run pkg_add in
            # dry mode and then look for 'not found (proceeding anyway)' in it. Yikes! :(
#            (PACKAGESITE=https://${CVS_SERVER_NAME}/packages/build/pub/FreeBSD/ports/${PLAT}/packages-${REL}-release/All/ pkg_add -r ${PKGNAME} && \
#            !(PACKAGESITE=https://${CVS_SERVER_NAME}/packages/build/pub/FreeBSD/ports/${PLAT}/packages-${REL}-release/All/ pkg_add -rnf ${PKGNAME} | grep 'not found (proceeding anyway)'))
            pkg install ${PKGNAME}  || (
                echo "Unable to install ${PKGNAME}.tbz"
                echo "Building $PKGNAME from source"
                ( make install -DFORCE_PKG_REGISTER ) || exit 1
                ( make $PACKAGE_RECURSIVE -DFORCE_PKG_REGISTER ) || exit 1
            )
        else
            ( make FORCE_PKG_REGISTER=yes install ) || exit 1
            ( make FORCE_PKG_REGISTER=yes package ) || exit 1
        fi
    fi
    cd $here
}
. ./freebsd_cross_build.sh

"*** Used to support code coverage feature ***"
. ./codeCoverage.sh

#freebsd_6_i386_gmake_check # XXX DJA

build_magic_db() {
                echo ""
                echo "Building magic database"
                ( cd $IPROOT/$IPPROD/packages/file539 && make PREFIX=$IPDATA -DNO_PKG_REGISTER -DINSTALL_AS_USER install ) || fail 1 "packages/file compilation failed"
}

install_magic_db() {
    # This should probably be done via a package.
    if [ $IPPROD = "phoebe" ]
    then
        srcdir=$IPDATA/share/file
        destdir=$DATA_DESTDIR/share/file
        install -d -o root -g wheel -m 0755 $destdir || fail 1 "Failed to make fingerprint directory."
        for file in $srcdir/magic.mgc \
                                $srcdir/fingerprints
        do
            install -o root -g wheel -m 0444 $file $destdir || fail 1 "Failed to copy $file"
        done
    fi
    src_path=`echo $IPDATA/lib/libmagic.so.* | xargs -n 1 | sort -n | tail -n 1`
    dest_path=$DATA_DESTDIR/lib/`basename $src_path`
    install -o root -g wheel -m 0555 $src_path $dest_path || fail 1 "Failed to copy $src_path"
}

install_sophos_ini() {

    echo "gjana#POS-12 : New sophos integration"
    source_ini_path=$IPROOT/coeus/packages/sophos.ini
    create_dirs $PACKAGE_DIR/data/third_party/sophos/
    dest_ini_path=$PACKAGE_DIR/data/third_party/sophos/
    install -o root -g wheel -m 0644 $source_ini_path $dest_ini_path || fail 1 "Failed to copy $source_ini_path"
}

install_smart_license_packages() {
   srcdir_tomcat=$IPROOT/coeus/packages/tomcat85
   TOMCAT_PREFIX=$PACKAGE_DIR/data/third_party/
   cd $srcdir_tomcat
   make clean deinstall install BATCH=yes PREFIX=$TOMCAT_PREFIX  || fail 1 "Failed to install 'apache tomcat85.'"

   TOMCAT_PKG_NAME="apache-tomcat-8.5"
   install -o root -g wheel -m 0755 $IPROOT/coeus/third_party/smartagent/smartagent.war $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/webapps || fail 1 "Failed to copy smartagent war file"
   rm -rf $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/conf/catalina.properties
   install -o root -g wheel -m 0755 $IPROOT/coeus/third_party/smartagent/conf/catalina.properties $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/conf || fail 1 "Failed to copy catalina.properties file"

   create_dirs $PACKAGE_DIR/data/third_party/smart_agent \
               $PACKAGE_DIR/data/third_party/smart_agent/conf \
               $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/webapps/smartagent \
               $PACKAGE_DIR/data/db/smart_license/agent_state

   tar -xvf $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/webapps/smartagent.war -C $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/webapps/smartagent

   mv $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/webapps/smartagent.war $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/webapps/smartagent.war.old

   install -o root -g wheel -m 0755 $IPROOT/coeus/third_party/smartagent/conf/smartagent.properties $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/lib || fail 1 "Failed top copy smartagent.properties to tomcat lib folder"

   install -o root -g wheel -m 0755 $IPROOT/coeus/third_party/smartagent/conf/smart_agent_config.json $PACKAGE_DIR/data/third_party/smart_agent/conf || fail 1 "Failed top copy smart_agent_config.json to $PACKAGE_DIR/data/third_party/smart_agent/conf"

   install -o root -g wheel -m 0755 $IPROOT/coeus/third_party/smartagent/conf/server.xml $PACKAGE_DIR/data/third_party/$TOMCAT_PKG_NAME/conf || fail 1 "Failed top copy server.xml to tomcat conf folder"
}

install_python() {
    build_magic_db
    echo "Compiling python..."
    export OPT="-g -O3 -DNDEBUG -fwrapv"
    if [ "x$sandbox_mode" = "x1" ]
    then
        (cd $IPROOT/coeus/stackless; ./godspeed-make.sh --with-coverage --configure-options="--without-doc-strings" --sandbox 2>&1) || fail 1 "python compilation failed"
    else
        (cd $IPROOT/coeus/stackless; ./godspeed-make.sh --with-coverage --configure-options="--without-doc-strings" 2>&1) || fail 1 "python compilation failed"
    fi
    /data/bin/python -c 'assert(2**64 == 18446744073709551616L)' > /dev/null 2>&1 || fail 1 "Python failed to build correctly"
    unset OPT
}

create_dirs() {
    # Note: install will only set the permission on the last directory if it
    # has to create intermediate directories.  Be careful.
    for d in "$@"
        do
            [ -d "$d" ] || install -d -o root -g wheel -m 0755 "$d" || fail 1 "Failed to create directory $d"
        done
}

create_ipoe() {
    PACKAGE_PATH=$1
    (cd $IPROOT/$PACKAGE_PATH || exit 1
     rm -rf build/ dist/
     #export LD_LIBRARY_PATH="/usr/local/lib";
     $IPDATA/bin/python setup.py install --root=build --optimize=2 \
     bdist_ipoe --exclude-source-files --exclude-pyc-files --exclude-files="demo-cert.txt,demo-key.txt,dh_2048.txt" || exit 1
     rm -rf *.egg-info
    ) || fail 1 "Could not create the package in $PACKAGE_PATH."
}

create_debug_ipoe() {
    PACKAGE_PATH=$1
    export LD_LIBRARY_PATH="/usr/local/lib";
    (cd $IPROOT/$PACKAGE_PATH; rm -rf build/;
        $IPDATA/bin/python setup.py egg_info -b_debug \
        bdist_ipoe --exclude-files="demo-cert.txt,demo-key.txt,dh_2048.txt"; \
        rm -rf *.egg-info) || \
        fail 1 "Could not create the debug package in $PACKAGE_PATH."
}

create_frozen_binary() {
    echo ""
    echo "Creating binaries..."

    # create the "translation" package __init__.py file
    (cd $IPROOT/$IPPROD/release/translation && make -j4 ) || \
        fail 1 "Failed to create package index for release/translation"

    # Install the python stdlib and third_party packages/modules
    cp -pR $PYTHON_LIB_DIR $DATA_DESTDIR/lib/
    # No "develop" on the appliances
    rm -f $PYTHON_DESTDIR/*.egg-link
    # XXX - huh?
    install -d -o root -g wheel -m 0555 $PYTHON_LIB_DIR $DATA_DESTDIR/

    # Rebuild the debug ipoe directory - the contents will be
    # repopulated below

    DEBUG_EGG_DESTDIR=$IPROOT/$IPPROD/release/debug_ipoe
    rm -rf $DEBUG_EGG_DESTDIR
    mkdir $DEBUG_EGG_DESTDIR
    install -d -o root -g wheel -m 0755 $DEBUG_EGG_DESTDIR

    # The install package is a little special. It cannot remove the .egg-info
    # directory since that is used to declare what type of package it is. In
    # addition, the package is never meant to end up on a translation other
    # than testing. Therefore, there is no debug package and it is not
    # optimized.
    (cd $IPROOT/ap/ipoe/install; rm -rf build/; rm -rf dist/;
        export LD_LIBRARY_PATH="/usr/local/lib";
        $IPDATA/bin/python setup.py bdist_ipoe;
        PYTHONPATH=$PYTHON_LIB_DIR/site-packages:$PYTHONPATH:$PYTHON_DESTDIR \
        $IPDATA/bin/python $IPROOT/ap/ipoe/install/ipoe_install.py \
            --install-dir $PYTHON_DESTDIR \
            `ls $IPROOT/ap/ipoe/install/dist/*nothr*.ipoe` ) || \
        fail 1 "Could not create ipoe_install package"

    # Install all IronPort packages
    # Note that the order here is *VERY* important, blame aquarium.
    # python_modules must be last because of sslip2 issues.
    for packagename in coeus \
                       coeus/python_modules/dns \
                       ap/shrapnel \
                       ap/aplib \
                       ap/evg \
                       ap/external_auth \
                       ap/ocsp \
                       ap/feedsd \
                       ap/ftpd \
                       ap/ginetd \
                       ap/ipblockd \
                       ap/heimdall \
                       ap/iccm \
                       ap/internal_resources \
                       ap/journal \
                       ap/kvm \
                       ap/mini_smtp \
                       ap/ntp \
                       ap/phone \
                       ap/qlog \
                       ap/reporting \
                       ap/reporting/tools \
                       ap/resmon \
                       ap/sandbox \
                       ap/scheduler \
                       ap/smad \
                       ap/snmp \
                       ap/ssh \
                       ap/support_request \
                       ap/timezones \
                       ap/updater_client \
                       ap/upgrades \
                       ap/vals \
                       ap/features \
                       ap/trusted_root_certs \
                       ap/vmtoolsd \
                       coeus/ui/webui/app \
                       coeus/ui/webui/app/site-packages \
                       coeus/ui/webui \
                       coeus/ui/webui/common-packages \
                       coeus/ui/webui/report-packages \
                       platform_reporting/reporting_ui/wsa \
                       platform_reporting/tracking_ui/wsa \
                       third_party/pyrad \
                       coeus/python_modules;
    do
        create_ipoe $packagename || fail 1 "Could not create $packagename"
        create_debug_ipoe $packagename || \
            fail 1 "Could not create $packagename_debug"
        for ipoe in `ls $IPROOT/$packagename/dist/*nothr*.ipoe`; do
            echo "Installing $ipoe at $PYTHON_DESTDIR"
            case "$ipoe" in
                *_debug*)
                    (cp $ipoe $DEBUG_EGG_DESTDIR) || fail 1 "Could not copy $ipoe"
                ;;
                *_packages* | *aquarium* | *ui_wsa*)
                    # Can't have the app and enduser site-package packages on
                    # the path by default or platform_reporting.
                    (PYTHONPATH=$PYTHON_LIB_DIR/site-packages:$PYTHONPATH:$PYTHON_DESTDIR \
                    $IPDATA/bin/python $IPROOT/ap/ipoe/install/ipoe_install.py \
                        --install-dir $PYTHON_DESTDIR -m \
                        $ipoe) || fail 1 "Could not install $ipoe"
                ;;
                *)
                    (PYTHONPATH=$PYTHON_LIB_DIR/site-packages:$PYTHONPATH:$PYTHON_DESTDIR \
                    $IPDATA/bin/python $IPROOT/ap/ipoe/install/ipoe_install.py \
                        --install-dir $PYTHON_DESTDIR \
                        $ipoe) || fail 1 "Could not install $ipoe"
                ;;
            esac
        done
    done

    ($IPDATA/bin/python $IPROOT/ap/ipoe/tools/build_frozen.py) || \
        fail 1 "Failed to freeze python source."
    # I have no idea .... just go with it.
    install -o root -g wheel -m 0555 $IPROOT/third_party/sleepycat_build/lib/libdb-4.4.so $DATA_DESTDIR/lib/ || fail 1 "Failed to install libdb"

    # Setup python-eggs temp directory.
    mkdir $DATA_DESTDIR/lib/python-eggs
    chmod a+w $DATA_DESTDIR/lib/python-eggs

    # Setup admin-python-eggs temp directory.
    mkdir $DATA_DESTDIR/lib/admin-python-eggs
    chmod a+w $DATA_DESTDIR/lib/admin-python-eggs

    # Setup smaduser-python-eggs temp directory.
    SMAD_EGGS_DIR=$DATA_DESTDIR/lib/smaduser-python-eggs
    SMAD_DIR_STR="smaduser ipoe directory"
    mkdir $SMAD_EGGS_DIR || fail 1 "Failed to create $SMAD_DIR_STR"
    chmod a+w $SMAD_EGGS_DIR || fail 1 "Failed to chmod $SMAD_DIR_STR"

    # distutils requires pyconfig.h to be on box
    mkdir -p $DATA_DESTDIR/include/python$PYTHON_VER
    install -o root -g wheel -m 0555 $IPDATA/include/python$PYTHON_VER/pyconfig.h $DATA_DESTDIR/include/python$PYTHON_VER/pyconfig.h
}

create_supplemental_binaries() {
    # No gmake...Mark and his silly BSD makefiles ;)
  if [ "x$sandbox_mode" != "x1" ]
  then
    (cp /usr/src/contrib/libpcap/pcap-int.h /usr/include/pcap-int.h) || fail 1 "Failed to copy pcap-int.h"
    (cp /usr/src/contrib/libpcap/portability.h /usr/include/portability.h) || fail 1 "Failed to copy portability.h"
        (cp /usr/src/contrib/libpcap/varattrs.h /usr/include/varattrs.h) || fail 1 "Failed to copy varattrs.h"
    (cd $IPROOT/coeus/misc/mfi ; make -j4 2>&1) || fail 1 "Failed to compile 'mfi_control'."
    (cd $IPROOT/coeus/misc/runas ; make -j4 2>&1) || fail 1 "Failed to compile 'runas'."
    patch -u -N $IPROOT/freebsd/mods/tools/tcp_stream/Makefile -i $IPROOT/coeus/packages/patches/patch-tcp_stream_Makefile
    (cd $IPROOT/freebsd/mods/tools/tcp_stream ; make -j4 2>&1) || fail 1 "Failed to compile 'tcp_stream'."
    (cd $IPROOT/coeus/misc/reset_cmos ; make -j4 2>&1) || fail 1 "Failed to compile 'reset_cmos'."
    (cd $IPROOT/coeus/smbios ; make -j4 2>&1) || fail 1 "Failed to compile 'smbios'."
  fi # !sandbox

    (cd $IPROOT/coeus/ui/webui/tools &&
     ./webui_build.sh) || fail 1 "Failed during webui_build.sh."

    (cd $IPROOT/coeus/share/locale && gmake depend )
    #(cd $IPROOT/$IPPROD/libvelocity && gmake )
    (cd $IPROOT/coeus/share/locale &&
     gmake -j4 app-build) ||
    fail 1 "Failed running share/locale/Makefile's app-build."

  if [ "x$sandbox_mode" != "x1" ]
  then
    (cd $IPROOT/coeus/misc/enablediag ; make -j4 2>&1) || fail 1 "Failed to compile 'enablediag'."
    (cd $IPROOT/coeus/misc/nextboot ; make -j4 2>&1) || fail 1 "Failed to compile 'nextboot'."

    (cd $IPROOT/coeus/commandd ; make -j4 2>&1) || fail 1 "Failed to compile 'command_proxy'."
  fi # !sandbox
}

create_merlin_binary() {
   echo ""
   echo "Creating merlin ..."
#   [ -f /usr/local/lib/libtcl84.a ] || package_build /usr/ports/lang/tcl84 || exit 1
   (export SCAN_DEFAULT_OVERRIDE="/none" \
        && freebsd_cross_do 6 i386 $IPROOT "[ -f /usr/local/lib/libtcl84.a ]") \
        || package_build_freebsd_cross 6 i386  /usr/ports/lang/tcl84 || exit 1
   (export COPY_ANYWAYS="yes"
    freebsd_cross_copy_in 6 i386 $IPROOT/merlin)
#   ( cd $IPROOT/merlin ; gmake -j4 all 2>&1 ) || fail 1 "Failed to compile 'merlin'."
   freebsd_cross_do 6 i386 $IPROOT/merlin "gmake -j4 all" || exit 1
   freebsd_cross_copy_out 6 i386 $IPROOT/merlin
   freebsd_cross_copy_out 6 i386 /data/bin merlin
   freebsd_cross_copy_out 6 i386 /data/etc merlin
   freebsd_cross_copy_out 6 i386 /data/db  merlin
   echo "Creating done merlin ..."
}

create_coeus_debug_tools() {
    ( cd $IPROOT/coeus/debug-tools/mtrace && gmake )
    cp $IPROOT/coeus/debug-tools/mtrace/libmtrace.so $DATA_DESTDIR/lib/libmtrace.so
}

install_coeus_perf_tools() {
    ( cd $IPROOT/freebsd/tests/aio; make -j4 2>&1 ) || fail 1 "Failed to compile 'aio'."
    install -o root -g wheel -m 0555 $IPROOT/freebsd/tests/aio/aio_kqueue $DATA_DESTDIR/bin/aio_kqueue || fail 1 "Failed to install 'aio_kqueue'."

    ( cd $IPROOT/freebsd/tests/aio/lio; make -j4 2>&1 ) || fail 1 "Failed to compile 'lio'."
    install -o root -g wheel -m 0555 $IPROOT/freebsd/tests/aio/lio/lio_kqueue $DATA_DESTDIR/bin/lio_kqueue || fail 1 "Failed to install 'lio_kqueue'."

    ( cd /usr/ports/benchmarks/netperf; make; make install; pkg create netperf; cd $DATA_DESTDIR; tar Jxvf /usr/ports/benchmarks/netperf/netperf-2.6.0_2.txz ) || fail 1 "Failed to install netperf"

    ( cd /usr/ports/benchmarks/raidtest; make; make install; pkg create raidtest; cd $DATA_DESTDIR; tar Jxvf /usr/ports/benchmarks/raidtest/raidtest-1.3.txz ) || fail 1 "Failed to install raidtest"

    ( cd $IPROOT/freebsd/tests/;  fetch https://engci-maven.cisco.com/artifactory/contentsecurity-group/Infra/flops-2.1_GH0.tar.gz; tar -xvf flops-2.1_GH0.tar.gz; cd flops-2.1; make -j4 2>&1 ) || fail 1 "Failed to compile 'flops'."
    install -o root -g wheel -m 0555 $IPROOT/freebsd/tests/flops-2.1/flops $DATA_DESTDIR/bin/flops || fail 1 "Failed to install 'flops'."

    ( cd $IPROOT/freebsd/tests/;  fetch https://engci-maven.cisco.com/artifactory/contentsecurity-group/Infra/pcm.tar.gz; tar -xvf pcm.tar.gz; cd pcm; gmake -j4 2>&1 ) || fail 1 "Failed to compile 'Intel pcm'."
    mkdir  $DATA_DESTDIR/pcm
    cp -a $IPROOT/freebsd/tests/pcm/*.x $DATA_DESTDIR/pcm || fail 1 "Failed to install pcm"
}

install_webcat() {
    PREFIX=/data/third_party/surfcontrol

  (export SCAN_DEFAULT_OVERRIDE="/none"
   export COPY_ANYWAYS="yes"
        freebsd_cross_copy_in 6 i386 $IPROOT/coeus/webcat
  ) || exit 1

    install -d -o root -g wheel -m 0755 $PACKAGE_DIR/$PREFIX/lib || fail 1 "Failed to make webcat lib."
    install -o root -g wheel -m 0444 $IPROOT/coeus/webcat/webcat/webcat_rpc_server.py $PACKAGE_DIR/$PREFIX/lib || fail 1 "Failed to install webcat_rpc_server.py"
}

create_https_utils_binaries() {
   echo ""
   echo "Creating new openssl_helper..."
   (cd $PROX_ROOT/../misc/https_utils &&
   sh ./deployUtils.sh $DATA_DESTDIR/bin/ ) || fail 1 "Failed to compile ised."
}

create_ised_binaries() {
   echo ""
   echo "Creating new ISED and Libs..."
   #poco library wants this version of libssl.so to be present in the lib repo, leaving other warnings as of now.
   destdir=/usr/lib/
   libdir=$IPROOT/coeus/release/reporting_deps
   cp $libdir/libssl.so.8 $destdir
   cp $libdir/libcrypto.so.8 $destdir

   (cd $PROX_ROOT/../nise/ &&
   sh ./deployISED.sh $DATA_DESTDIR/  $DATA_DESTDIR/nise/ ) || fail 1 "Failed to compile ised."

   install -d -o root -g wheel -m 0755 /usr/local/libcommon_ise /data/nise/ise_daemon || fail 1 "Failed to give permission to ise daemon and lib"
}

package_build_nats_server(){
    package_nats=$IPROOT/coeus/packages/nats-server
    echo "Starting `date` package_build_nats_server (app_build.sh) $package_nats"
    here=`pwd`
    [ -d $package_nats ] || (echo "Directory $package_nats DOES NOT exists; So creating" && (mkdir -p $package_nats))
    cd $package_nats
    (fetch -T 60 https://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/nats-server-v2.9.11-freebsd-amd64.tar.gz) || exit 1
    (tar -xvf nats-server-v2.9.11-freebsd-amd64.tar.gz) || exit 1
    mkdir -p $DATA_DESTDIR/bin/nats-server
    #mkdir -p /data/bin/nats-server
    install -o root -g wheel -m 0755 nats-server-v2.9.11-freebsd-amd64/* $DATA_DESTDIR/bin/nats-server/ || fail 1 "Failed to copy nats server"
    #(cp -r nats-server-v2.9.11-freebsd-amd64/* /data/bin/nats-server/) || exit 1
    cd $here
    echo "Ending `date` package_build $package_nats"
}

package_build_protobuf(){
    here=`pwd`
    echo "Building protobuf for nats-client dependency"
    ( cd $IPROOT/$IPPROD/packages/protobuf.nats && make clean && make && make install)
    ( cd $IPROOT/$IPPROD/packages/protobuf.nats/work/protobuf-3.5.1 && make && make install)
    cd $here
    echo "Package protobuf installation done"
}

package_build_protobuf_c(){
    here=`pwd`
    echo "Building protobuf-c for nats-client dependency"
    ( cd $IPROOT/$IPPROD/packages/protobuf-c && make clean && make && make install)
    cd $here
    echo "Package protobuf-c installation done"
}

package_build_nats_client(){
    here=`pwd`
    package_natc=$IPROOT/coeus/packages/nats-client
    echo "Starting `date` package_build_nats_client (app_build.sh) $package_natc"
    cd $package_natc
    (fetch -T 60 https://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/nats.c-3.5.0.tar.gz) || exit 1
    [ -d nats.c-3.5.0 ] && (echo "Deleting nats.c-3.5.0 directory" && (rm -rf nats.c-3.5.0))
    (tar -xvf nats.c-3.5.0.tar.gz) || exit 1
    cd nats.c-3.5.0
    patch < ../patch/nats.c.sockpatch
    mkdir build
    cd build
    (/usr/local/cmake-3.20.1/bin/cmake .. -DNATS_BUILD_STREAMING=OFF -DNATS_BUILD_WITH_TLS=OFF) || exit 1
    make install
    install -o root -g wheel -m 0755 /usr/local/lib/libnats.* $DATA_DESTDIR/lib/ || fail 1 "Failed to copy libnats files"
    cd $here
    echo "Ending `date` package_build $package_natc"
}

package_build_bitdefender() {
    echo "Installing log4cplus as dependency for bitdefender"
    (package_build /usr/ports/devel/log4cplus) || fail 1 "log4cplus installation failed"
    here=`pwd`
    package_bd_home=$IPROOT/coeus/bitdefender
    package_bd=$IPROOT/coeus/bitdefender/src
    package_bd_config=$IPROOT/coeus/bitdefender/config
    BITDEFENDER_INSTALL_PATH=$PACKAGE_DIR/data/third_party/bitdefender
    BITDEFENDER_SSE_PATH=$BITDEFENDER_INSTALL_PATH/sse
    BITDEFENDER_SDK_PATH=$BITDEFENDER_INSTALL_PATH/sdk/factory
    BITDEFENDER_LOG_PATH=$BITDEFENDER_INSTALL_PATH/logs
    mkdir -p $BITDEFENDER_INSTALL_PATH
    mkdir -p $BITDEFENDER_SSE_PATH
    mkdir -p $BITDEFENDER_SDK_PATH
    mkdir -p $BITDEFENDER_LOG_PATH
    echo "Starting `date` package_build_bitdefender (app_build.sh) $package_bd"
    cd $package_bd_config
    install -o root -g wheel -m 0755 bd_config.yaml $BITDEFENDER_INSTALL_PATH || fail 1 "Failed to copy bd_config.yaml file"
    install -o root -g wheel -m 0755 bitdefender.sse $BITDEFENDER_SSE_PATH || fail 1 "Failed to copy bitdefender.sse file"
    cd $package_bd
    make clean && make
    install -o root -g wheel -m 0755 bitdefender $BITDEFENDER_INSTALL_PATH || fail 1 "Failed to copy bitdefender files"
    cd $package_bd_home
    cp -r SDK/bin $BITDEFENDER_SDK_PATH/ || fail 1 "Failed to copy sdk files"
    cp -r heimdall $BITDEFENDER_INSTALL_PATH/ || fail 1 "Failed to copy sdk files"
    cd $here
    echo "Ending `date` package_build $package_bd"
}

package_build_cxxopts(){
    here=`pwd`
    package_cxxopts=$IPROOT/coeus/packages/cxxopts
    echo "Starting `date` package_build_cxxopts (app_build.sh) $package_cxxopts"
    [ -d $package_cxxopts ] || (echo "Directory $package_cxxopts DOES NOT exists; So creating" && (mkdir -p $package_cxxopts))
    cd $package_cxxopts
    (fetch -T 60 https://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/cxxopts-3.1.1.tar.gz) || exit 1
    [ -d cxxopts-3.1.1 ] && (echo "Deleting cxxopts-3.1.1 directory" && (rm -rf cxxopts-3.1.1))
    (tar -xvf cxxopts-3.1.1.tar.gz) || exit 1
    cd cxxopts-3.1.1
    (/usr/local/cmake-3.20.1/bin/cmake -Bbuild -H.) || exit 1
    (/usr/local/cmake-3.20.1/bin/cmake --build build/ --target install) || exit 1
    cd $here
    echo "Ending `date` package_build $package_cxxopts"
}

package_build_yaml_cpp(){
    here=`pwd`
    package_yaml_cpp=$IPROOT/coeus/packages/yaml-cpp
    echo "Starting `date` package_build_yaml_cpp (app_build.sh) $package_yaml_cpp"
    [ -d $package_yaml_cpp ] || (echo "Directory $package_yaml_cpp DOES NOT exists; So creating" && (mkdir -p $package_yaml_cpp))
    cd $package_yaml_cpp
    (fetch -T 60 https://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/yaml-cpp-yaml-cpp-0.6.0.tar.gz) || exit 1
    [ -d yaml-cpp-yaml-cpp-0.6.0 ] && (echo "Deleting yaml-cpp-yaml-cpp-0.6.0 directory" && (rm -rf yaml-cpp-yaml-cpp-0.6.0))
    (tar -xvf yaml-cpp-yaml-cpp-0.6.0.tar.gz) || exit 1
    cd yaml-cpp-yaml-cpp-0.6.0
    (/usr/local/cmake-3.20.1/bin/cmake -Bbuild -H. -DYAML_CPP_BUILD_TESTS=OFF) || exit 1
    (/usr/local/cmake-3.20.1/bin/cmake --build build/ --target install) || exit 1
    cd $here
    echo "Ending `date` package_build $package_yaml_cpp"
}

create_prox_binaries() {

   (package_build /usr/ports/dns/udns) || fail 1 "udns installation failed while building prox binaries"
   (package_build /usr/ports/devel/gperf) || fail 1 "gperf installation failed while building prox binaries"
   uname -a
   if [ `uname -r | sed 's/\..*$//'` -lt 10 ]
   then
     (package_build $IPROOT/coeus/packages/glib20.old) || fail 1 "glib20 installation failed while building lasso"
   else
     (package_build $IPROOT/coeus/packages/glib20) || fail 1 "glib20 installation failed while building lasso"
   fi

   echo "Building Chimera client..."
   (cd $IPROOT/coeus/chimera/base64 && gmake) || fail 1 "chimera-client: base64 library build failure."
   (cd $IPROOT/coeus/chimera/cJSON && gmake) || fail 1 "chimera-client: cJSON library build failure."

   echo "Building symmetric library ..."
   (cd $IPROOT/coeus/misc/symmetric && gmake) || fail 1 "symmetric library build failure."
   # Builds static libraries... dont need to be copied.

   echo ""
   echo "Creating prox..."
   (cd $PROX_ROOT && gmake -j4 app-build) || fail 1 "Failed to compile 'prox'."

   chmod 0644 $PACKAGE_DIR/usr/local/prox/etc/magic.mime || fail 1 "Failed to change permissions."
   chmod 0644 $PACKAGE_DIR/usr/local/prox/etc/magic_v5.mime || fail 1 "Failed to change permissions."
   chmod 0644 $PACKAGE_DIR/usr/local/prox/etc/magic_v8.mgc || fail 1 "Failed to change permissions."

   to=$PACKAGE_DIR/data/pub/track_stats

   # XXX: Should this be "log" group and be group-writeable?
   install -d -o root -g wheel -m 0755 $to/ || fail 1 "Failed to make track_stats"
   echo "This directory contains the tracking stats information for proxy." >> $to/README || fail 1 "Failed to make track_stats README"
   chown 0:0 $to/README || fail 1 "Failed to chown track_stats README"

   to=$PACKAGE_DIR/data/db/pacserv

   install -d -o root -g wheel -m 0755 $to/ || fail 1 "Failed to make pacserv"
   echo "This directory contains the Proxy Auto-Configuration (PAC) files." >> $to/README || fail 1 "Failed to make pacserv README"
   chown 0:0 $to/README || fail 1 "Failed to chown pacserv README"

}

install_prox_mib_agent() {
    destdir=$DATA_DESTDIR/bin
    ( cd $IPROOT/coeus/prox/prox_mib && gmake || ( fail 1 "Failed to compile prox_mib_agent!" ) )
    cp -f $IPROOT/coeus/prox/prox_mib/prox_mib_agent $destdir || exit 1
}

temp_third_party_utils_copy() {
    destdir=$DATA_DESTDIR/bin
    cp -f $IPROOT/scanners/third_party_utils.py $destdir
    cp -f $IPROOT/scanners/picklelog_client.py $destdir
}

link_or_copy_or_fail () {
    # link (or failing that, copy and in future link to this copy)
    #
    # the variable named by the first argument is reserved for
    # keeping the name to the "closest" file to duplicate.

    user=$1
    group=$2
    perm=$3
    component=$4
    dest=$5

    eval original=\$$component

    if [ "$original" != "$dest" ]
    then
        if ln -f $original $dest
        then
            # yay
            chown $user:$group $dest
            chmod $perm $dest
        else
            rm -f $dest > /dev/null 2>&1
            cp $original $dest || fail 1 "Failed to install `basename $dest`"
            eval $component=$original
        fi
    fi
}

install_svc() {
    (
    local src="$1"
    local dst="$2"
    local level="$3"
    local basename="`basename $src`"
    local suffix="${4:-$basename}"
    install -m 755 $src $dst/$level$suffix
    ) || fail 1 "Failed to copy $basename"
}

install_binaries() {
    echo ""
    echo "Installing binaries in $PACKAGE_DIR ..."

  if [ "x$sandbox_mode" = "x1" ]
  then
    bin_apps="
        commandd
        sandbox
        setup_config
        upgrade_helper
        ipoe_install
        "
  else
    libexec_apps="
        cli
        smad_cli
        generate_dtd
        raid_log_watch
        core_watch
        "
    bin_apps="
        hermes
        sntpd
        ftpd.main
        clear_prox_cache
        commandd
        interface_controller
        interface_log_watch
        ginetd
        heimdall
        heimdall_svc
        ipblockd
        setup_config
        qabackdoor
        gui
        talos_intelligence
        ytc
        ipkey_test
        null_server
        command_client
        upgrade.image.reader
        upgrade.client.upgrade_client
        upgrade.client.upgrade_log
        upgrade.client.cleanup_download
        passthroughd
        snmp.passthrough_client
        ts
        qlog_xml_doc
        coeuslogd
        gatherer
        updaterd
        configdefragd
        coeus_params
        webcatd
        wbrsd_startup
        firestone_monitor
        counterd
        counterd_master
        reportd
        reportqueryd
        reportd_helper
        reporting_wdog
        sandbox
        sophos_monitor
        upgrade_helper
        revert_cleanup
        check_fips_cert
        get_config_var
        thirdparty
        trafmon
        mgmtfw
        shd
        test_auth_realm
        test_ntlm_auth
        create_computer_object
        proxy_monitor
        pacd
        sicapd
        extauth_rpc_wdog
        external_auth_log
        local_authd
        local_authd_wdog
        qlogd
        qlogd_wdog
        ipoe_install
        ocspd
        ocspd_wdog
        feedsd
        feedsd_wdog
        uds
        uds_wdog
        samld
        avc_monitor
        musd
        vmtoolsd
        ldap_rpc_server
        ldap_rpc_wdog
        webcat_monitor
        wbrsd_monitor
        mcafee_monitor
        webroot_monitor
        amp_monitor
        webtapd_monitor
        winbindd_watch
        prox_mib_agent_monitor
        ised_monitor
        hybridd
        hybridd_wdog
        sse_connectord
        sse_connectord_wdog
        csid
        csid_wdog
        archivescan_monitor
        generate_adminpassword
        policyinspectord
        policyinspectord_wdog
        sl_usercountd
        sl_usercountd_wdog
        smart_agent_wdog
        features.smartlicense_feature
        api_server
        replicatord
        replicatord_wdog
        ytc_monitor
        arsd
        arsd_wdog
        umbrella_client_wdog
        report_shipper_client_wdog
        adc_monitor
        bitdefender_monitor
        "
  fi # !sandbox

    for app in $libexec_apps
    do
        link_or_copy_or_fail 0 0 0555 BOOTSTRAP $DATA_DESTDIR/libexec/$app
    done
    for app in $bin_apps
    do
        link_or_copy_or_fail 0 0 0555 BOOTSTRAP $DATA_DESTDIR/bin/$app
    done

  if [ "x$sandbox_mode" != "x1" ]
  then
    # Create fancy links for scanners too!
    oldcwd=`pwd`
    cd $IPROOT/scanners || fail 1 "Failed to cd into scanners."
    make who_links_to_stackless
    for app in `cat who_links_to_stackless`
    do
        link_or_copy_or_fail 0 0 0555 BOOTSTRAP $DATA_DESTDIR/bin/$app
    done
    cd $oldcwd

    install -o root -g wheel -m 4555 $IPROOT/coeus/misc/runas/runas $DATA_DESTDIR/bin/runas || fail 1 "Failed to install 'runas'."
    install -o root -g wheel -m 4555 $IPROOT/freebsd/mods/tools/tcp_stream/tcp_stream $DATA_DESTDIR/bin/tcp_stream || fail 1 "Failed to install 'tcp_stream'."
    install -o root -g wheel -m 0555 $IPROOT/coeus/misc/reset_cmos/reset_cmos $DATA_DESTDIR/bin/reset_cmos || fail 1 "Failed to install 'reset_cmos'."
    ( cd $IPROOT/coeus/misc/megatool/amr_control && make -j4 DESTDIR=$DATA_DESTDIR install ) || fail 1 "Failed to install 'amr_control utilities'."
    ( cd $IPROOT/coeus/misc/megacli && make -j4 DESTDIR=$DATA_DESTDIR install ) || fail 1 "Failed to install 'MegaCli'."
    ( cd $IPROOT/coeus/misc/storcli && make -j4 DESTDIR=$DATA_DESTDIR install ) || fail 1 "Failed to install 'StorCli'."
    ( cd $IPROOT/coeus/misc/mfi && make -j4 DESTDIR=$DATA_DESTDIR/bin install ) || fail 1 "Failed to install 'mfi_control'."
   #( cd $IPROOT/coeus/misc/is_alive && make -j4 DESTDIR=$DATA_DESTDIR install ) || fail 1 "Failed to install 'is_alive'."
    install -o root -g wheel -m 0555 $IPROOT/coeus/smbios/smbios $DATA_DESTDIR/bin/smbios || fail 1 "Failed to install 'smbios'."
    install -o root -g wheel -m 0555 $IPROOT/coeus/aaccli/aaccli $DATA_DESTDIR/bin/aaccli || fail 1 "Failed to install 'aaccli'."
    #link_or_copy_or_fail 0 0 0555 BOOTSTRAP $DATA_DESTDIR/bin/configinit
    #link_or_copy_or_fail 0 0 0555 BOOTSTRAP $DATA_DESTDIR/bin/rps_collector
  fi # !sandbox

}

install_startup_scripts() {
    # copy startup scripts
    echo "Copying startup scripts..."
    from=$IPROOT/freebsd/bootstrap
    to=$DATA_DESTDIR/etc/rc.d/

    install -d -o root -g wheel -m 0755 $to || fail 1 "Failed to create $to"

    bin_scripts="
        killer.sh
        sshtunnel.py
        ipmitool.py
        core_reaper.sh
        supportrequest.sh
        check_and_reset_cmos.sh
        queue_rebuild.sh
        reload.sh
        revert.sh
        revert_utils.sh
        tcpdump.sh
        killptree.sh
        wsa_snap.sh
        notty.py
        source_asyncos_wrapper.sh
        system_killer.sh
        bd_cmd.py
        bd_where_all
        interface_update.py
        bd_get_prof
        "
    rc_d_scripts="
        config.sh:000_config.sh
        keygen.sh:010_keygen.sh
        vm_init.sh:010_vm_init.sh
        roll_logs.sh:050_roll_logs.sh
        verify_logs.sh:051_verify_logs.sh
        a_raid_type.sh:110_raid_type.sh
        watchdogd.sh:120_watchdogd.sh
        expand.sh:200_expand.sh
        config_mfi.sh:0000_config_mfi.sh
        prox_keyinstall.sh:120_prox_keyinstall.sh
        nextboot.sh
        welcome.sh
        z_raid_status.sh
        haswell
        turboboost
        generate_dtd.sh
        gettytab_failsafe
        lldp_config.sh
        "

    for script in $rc_d_scripts
    do
      # if the script is of the format FOO:BAR, we install FOO as BAR,
      # otherwise we install FOO as FOO.
      alias=$(expr $script : '.*:\(.*\)')
      script=$(expr $script : '\([^:]*\)')
      [ -z "$alias" ] && alias=$script
      install -o root -g wheel -m 0555 $from/$script $to/$alias || fail 1 "Failed to copy $script"
    done

    for bin in $bin_scripts
    do
      install -o root -g wheel -m 0555 $from/$bin $DATA_DESTDIR/bin/$bin || fail 1 "Failed to copy $bin"
    done

    log_analysis_scripts="
        MainParser.py
        ApacheParser.py
        SquidParser.py
        SquidExtParser.py
        logFormat.py
        AvgObjectSize.py
        RequestRatePerSec.py
        ScanBladeAvgObjectSize.py
        ScanBladePercentage.py
        NumberOfUniqueIPs.py
        NumberOfUniqueUsers.py
        timestampSort.py
        WrongLogFormatException.py
        "
    for f in $log_analysis_scripts
    do
        install -o root -g wheel -m 0755 $IPROOT/$IPPROD/misc/log_analysis/$f $DATA_DESTDIR/bin/$f || fail 1 "Failed to copy $f"
    done

    ae_cs_troubleshooting_scripts="
        tracksum2.py
        acsum.py
        describe_aclog.py
        pingntlm.py
        "
    for f in $ae_cs_troubleshooting_scripts
    do
        install -o root -g wheel -m 0755 $IPROOT/$IPPROD/tools/$f $DATA_DESTDIR/bin/$f || fail 1 "Failed to copy $f"
    done

    authdiag_scripts="
        ldapdump
        ldapquery
        ntlmdump
        ntlmquery
        authdiag_env.sh
        authdiag_fns.sh
        authdiag_ntlmfns.sh
        "
    for f in $authdiag_scripts
    do
        install -o root -g wheel -m 0755 $IPROOT/$IPPROD/misc/authdiag/$f $DATA_DESTDIR/bin/$f || fail 1 "Failed to copy $f"
    done

    install -o root -g wheel -m 0555 $IPROOT/coeus/qabackdoor/qabackdoor.sh $to/ || fail 1 "Failed to copy qabackdoor.sh"

    install -o root -g wheel -m 0555 $IPROOT/ap/heimdall/rc.d/heimdall.sh $to/ || fail 1 "Failed to copy heimdall.sh"

    install -o root -g wheel -m 0755 $IPROOT/coeus/packages/nats-server/rc.d/nats_server $to/ || fail 1 "Failed to copy nats_server.sh"

    #mkdir -p $DATA_DESTDIR/etc/telegraf/templates
    #install -o root -g wheel -m 0755 $IPROOT/coeus/packages/telegraf/telegraf_template.conf $DATA_DESTDIR/etc/telegraf/templates/ || fail 1 "Failed to copy telegraf_template.conf"
    #install -o root -g wheel -m 0555 $IPROOT/coeus/packages/cloudinit/rc.d/cloudinit $to/ || fail 1 "Failed to copy cloudinit"
    #install -o root -g wheel -m 0755 $IPROOT/coeus/packages/cloudinit/cloudinit.py $DATA_DESTDIR/bin/ || fail 1 "Failed to copy cloudinit.py"
    #install -o root -g wheel -m 0555 $IPROOT/coeus/packages/cloudinit/rc.d/configinit $to/ || fail 1 "Failed to copy configinit"
    #install -o root -g wheel -m 0555 $IPROOT/coeus/packages/telegraf/rc.d/telegraf $to/ || fail 1 "Failed to copy telegraf"
    #install -o root -g wheel -m 0755 $IPROOT/coeus/packages/s3_server/s3_server.py $DATA_DESTDIR/bin/ || fail 1 "Failed to copy s3_server.py"
    #install -o root -g wheel -m 0755 $IPROOT/coeus/packages/s3_server/rc.d/s3_server_setup $to/ || fail 1 "Failed to copy s3_server_setup"
    to=$DATA_DESTDIR/etc/heimdall/
    install -d -o root -g wheel -m 0755 $to || fail 1 "Failed to create $to"

    # The following are installed via their packages.
    #third_party/brightmail/SDK/ironport/heimdall/brightmail
    #third_party/case/heimdall/case
    #third_party/scanners/cloudmark/heimdall/cloudmark
    #third_party/scanners/commtouch/heimdall/commtouch
    #third_party/scanners/mcafee/heimdall/mcafee
    #third_party/scanners/stellent/heimdall/stellent
    #third_party/sophos/heimdall/sophos
    for file in freebsd/bootstrap/heimdall/sshtunnel \
                freebsd/bootstrap/heimdall/ipmitool \
                coeus/commandd/heimdall/commandd \
                coeus/hermes/heimdall/interface_controller \
                coeus/hermes/heimdall/hermes \
                coeus/hermes/heimdall/top \
                coeus/beaker/heimdall/talos_intelligence \
                coeus/ytc/heimdall/ytc \
                ap/reporting/heimdall/reportd \
                ap/reporting/heimdall/reportd_helper \
                ap/reporting/heimdall/reportqueryd \
                ap/reporting/heimdall/counterd_master \
                ap/reporting/heimdall/haystackd \
                ap/ntp/heimdall/sntpd \
                ap/ftpd/heimdall/ftpd \
                ap/ocsp/heimdall/ocspd \
                ap/feedsd/heimdall/feedsd \
                ap/ginetd/heimdall/ginetd \
                ap/ipblockd/heimdall/ipblockd \
                ap/vmtoolsd/heimdall/vmtoolsd \
                coeus/ui/webui/app/heimdall/gui \
                coeus/third_party/heimdall/thirdparty \
                ap/updater_client/heimdall/updaterd \
                ap/snmp/heimdall/snmpd \
                ap/snmp/heimdall/passthroughd \
                $IPPROD/api/heimdall/api_server \
                coeus/firestone/heimdall/firestone \
                scanners/webroot/heimdall/merlin \
                scanners/webtapd/heimdall/webtapd_replicator \
                coeus/webcat/heimdall/webcat_rpc_server \
                coeus/configdefragd/heimdall/configdefragd \
                coeus/coeuslog/heimdall/coeuslogd \
                coeus/gatherer/heimdall/gathererd \
                coeus/webcat/heimdall/webcatd \
                coeus/wbrs/heimdall/wbrsd \
                coeus/system_health/heimdall/shd \
                coeus/traffic_monitor/heimdall/trafmon \
                coeus/mgmtfw/heimdall/mgmtfw \
                coeus/third_party/redis/heimdall/redis-server \
                coeus/chimera-server/heimdall/chimera \
                coeus/chimera-server/heimdall/nectar \
                coeus/quotacache/heimdall/quotacache \
                coeus/cstat/heimdall/cstat-redis-server \
                coeus/prox/heimdall/prox \
                coeus/prox/heimdall/wccpd \
                coeus/pacd/heimdall/pacd \
                coeus/sicapd/heimdall/sicapd \
                ap/external_auth/heimdall/external_auth_rpc_server \
                ap/ntp/heimdall/sntpd \
                ap/external_auth/heimdall/local_authd \
                scanners/fire_amp/heimdall/amp \
                scanners/fire_amp/heimdall/amp_redis_server \
                ap/qlog/heimdall/qlogd \
                ap/sandbox/heimdall/sandboxd \
                coeus/samld/heimdall/samld \
                coeus/uds/heimdall/uds \
                coeus/avc/heimdall/avc \
                coeus/musd/heimdall/musd \
                ap/external_auth/heimdall/ldap_rpc_server \
                coeus/archivescan/heimdall/archivescan \
                coeus/ised/heimdall/ised \
                coeus/ised/heimdall/ised2 \
                coeus/hybrid/heimdall/hybridd \
                coeus/sse_connector/heimdall/sse_connectord \
                coeus/csi/heimdall/csid \
                coeus/policyinspectord/heimdall/policyinspectord \
                coeus/sl_usercountd/heimdall/sl_usercountd \
                coeus/prox/prox_mib/heimdall/prox_mib_agent \
                $IPPROD/third_party/smartagent/heimdall/smart_agent \
                third_party/nginx/heimdall/trailblazer \
                coeus/replicatord/heimdall/replicatord \
                coeus/arsd/heimdall/arsd \
                coeus/adc/heimdall/adc \
                coeus/bitdefender/heimdall/bitdefender \
                ;
    do
        base=`basename $file`
        install -o root -g wheel -m 0444 $IPROOT/${file}_release.conf $to/${base}.conf || fail 1 "Failed to copy ${file}_release.conf"
    done

    to=$DATA_DESTDIR/bin/
    for script in cli \
                  cli.sh \
                  smad_cli.sh \
                  command_proxy.sh \
                  raid_log_watch \
                  raid_log_watch.sh \
                  core_watch.sh
    do
        link_or_copy_or_fail 0 0 0555 WRAPPER $to/$script
    done

    unset from to
}

install_csborg_script() {
    from=$IPROOT/ap/reporting/scripts/cs-borg-dc
    to=$DATA_DESTDIR/bin

    # make cs-borg-data-collector
    cd $from
    ./make_csborg.sh
    cd -

    # copy cs-borg-data-collector

    echo "Copying cs-borg-data-collector..."

    install -o root -g wheel -m 0555 $from/cs-borg-data-collector $to/cs-borg-data-collector || fail 1 "Failed to copy cs-borg-data-collector"

    unset from to
}

install_enablediag() {
    # copy everything enablediag related

    echo "Copying enablediag..."

    from=$IPROOT/coeus/misc/enablediag
    to=$DATA_DESTDIR/bin/

    install -o root -g wheel -m 0555 $from/enablediagnostics.sh $to/enablediagnostics.sh || fail 1 "Failed to copy enablediagnostics.sh"
    install -o root -g wheel -m 0555 $from/enablediag.sh $to/enablediag.sh || fail 1 "Failed to copy enablediag.sh"
    install -o root -g wheel -m 0555 $from/do_crypt $to/do_crypt || fail 1 "Failed to copy do_crypt"

    unset from to
}

install_wbrs() {
    echo "Installing wbrs..."
    $IPROOT/coeus/wbrs/install-wbrsd-pkg.sh -n 'factory' \
                                            -d $IPROOT/coeus/wbrs/db.tgz \
                                            $IPROOT/coeus/wbrs/wbrsd.tgz

    echo "Copying wbrs files..."
    from=$IPDATA/db/wbrs
    to=$PACKAGE_DIR/data/db/wbrs

    test -e $from/factory || fail 1 "$from/factory does not exist"

    if [ -e $to ]; then
        rm -rf $to
    fi
    install -d -o root -g wheel -m 0755 $to || fail 1 "Failed to create $to"

    cp -R $from/factory $to/factory || fail 1 "Failed to copy factory wbrs"
    #chown -R root:wheel $to || fail 1 "Failed to chown wbrs"
    (cd $to ; ln -sf factory current) || fail 1 "Failed to symlink factory wbrs"

    unset from to
 }

install_firestone() {
        cd $IPROOT/$IPPROD/release
        ./engine_install.sh --prefix=$PACKAGE_DIR --firestone || fail 1 "failed to install firestone"
}

install_avc_engine() {
        echo "JWAL : avc_engine"
         mkdir -p $DATA_DESTDIR/etc/avc || fail 1 "Failed to make AVC etc dir"
        ./engine_install.sh --prefix=$PACKAGE_DIR --avc_engine || fail 1 "Failed to install avc_engine"
        cp $IPROOT/$IPPROD/avc/avc.ini  $DATA_DESTDIR/etc/avc/
        cp $IPROOT/$IPPROD/avc/socket.py  /usr/local/lib/python2.6_13_amd64_thr/
        echo "JWAL : avc_engine end "
}

install_default_tm_blacklist() {
    from=$IPROOT/coeus/traffic_monitor/data
    to=$PACKAGE_DIR/data/db/trafmon
    filename="blacklist.data"

    install -d -o root -g wheel -m 0644 $to || fail 1 "Failed to create $to"
    install -o root -g wheel -m 0644 $from/$filename $to/$filename || fail 1 "Failed to copy $wbrs_file"

    unset from to filename
 }

install_adaptive_scanning() {
    destination_dir=$DATA_DESTDIR/etc/as
    source_dir=$IPROOT/coeus/adaptive_scanning

    echo "Copying AS SSE config"
    mkdir -p $destination_dir || fail 1 "Failed to create $destination_dir"
    # only one file for now
    for f in as.sse
    do
        install -o root -g wheel -m 0644 $source_dir/$f $destination_dir/$f || fail 1 "Failed to copy $f"
    done
}

install_onbox_dlp() {
    destination_dir=$DATA_DESTDIR/etc/onboxdlp
    source_dir=$IPROOT/coeus/onboxdlp

    echo "Copying onbox SSE config"
    mkdir -p $destination_dir || fail 1 "Failed to create $destination_dir"
    # only one file for now
    for f in onbox_dlp.sse
    do
        install -o root -g wheel -m 0644 $source_dir/$f $destination_dir/$f || fail 1 "Failed to copy $f"
    done
}

install_archive_scanner() {
    destination_dir=$DATA_DESTDIR/etc/archivescan
    source_dir=$IPROOT/coeus/archivescan

    echo "Creating archive_scan binary"
    destdir=$DATA_DESTDIR/bin
    ( cd $source_dir && gmake clean all || ( fail 1 "Failed to compile ArchiveScanner" ) )
    cp -f $source_dir/archive_scan $destdir || exit 1
    echo "Copied archive_scan binary"

    #echo "Creating archive_scan.cov binary"
    #destdir=$DATA_DESTDIR/bin
    #( cd $source_dir && gmake archive_scan.cov )
    #cp -f $source_dir/archive_scan.cov $destdir
    #echo "Copied archive_scan.cov binary"

    echo "Copying ArchiveScan SSE config"
    mkdir -p $destination_dir || fail 1 "Failed to create $destination_dir"
    # only one file for now
    for f in archivescan.sse
    do
        install -o root -g wheel -m 0644 $source_dir/$f $destination_dir/$f || fail 1 "Failed to copy $f"
    done
}

install_webtapd() {
    destination_dir=$DATA_DESTDIR/etc/webtapd
    source_dir=$IPROOT/scanners/webtapd
    build_dir=$IPROOT/scanners/webtapd/webtapd

    echo "Building prox_staging.so for WebTapD"
    ( cd $build_dir && gmake clean all || ( fail 1 "Failed to compile prox_staging.so" ) )

    echo "Copying WebTapd SSE config and conf template"
    mkdir -p $destination_dir || fail 1 "Failed to create $destination_dir"
    # 2 files - the sse and template conf - removed sse
    for f in webtapd_template.conf
    do
        install -o root -g wheel -m 0644 $source_dir/$f $destination_dir/$f || fail 1 "Failed to copy $f"
    done
    cp -f $build_dir/prox_staging.so $destination_dir|| exit 1
    echo "Copied WebTapD prox_staging.so"
}

download_prebuilt_packages() {
    (cd $IPROOT/coeus/third_party && bash download_prebuild_packages.sh $DATA_DESTDIR)
    # Being here means redis is been compiled and available on dev box.
    # So copy redis-server binary as chimera-server to destination.
    cp $IPROOT/coeus/third_party/redis_fbsd10_4/result/bin/redis-server $DATA_DESTDIR/bin/chimera
    # Also copy chimera config file.
    cp $IPROOT/coeus/chimera-server/conf.chimera-server $DATA_DESTDIR/etc/chimera.conf
    # chimera-cli is wrapper for redis-cli.
    cp $IPROOT/coeus/chimera/chimera-cli $DATA_DESTDIR/bin/chimera-cli
    chmod 755 $DATA_DESTDIR/bin/chimera-cli

    # changes for nectar.
    cp $IPROOT/coeus/third_party/redis_fbsd10_4/result/bin/redis-server $DATA_DESTDIR/bin/nectar
    cp $IPROOT/coeus/chimera-server/conf.nectar-server $DATA_DESTDIR/etc/nectar.conf
    cp $IPROOT/coeus/chimera/nectar-cli $DATA_DESTDIR/bin/nectar-cli
    chmod 755 $DATA_DESTDIR/bin/nectar-cli

    # changes for quotacache
    cp $IPROOT/coeus/quotacache/conf.quotacache $DATA_DESTDIR/etc/quotacache.conf
    cp $IPROOT/coeus/quotacache/quotacache-cli $DATA_DESTDIR/bin/quotacache-cli
    chmod 755 $DATA_DESTDIR/bin/quotacache-cli

    # changes for cstat.
    cp $IPROOT/coeus/third_party/redis_fbsd10_4/result/bin/redis-server $DATA_DESTDIR/bin/cstat-redis-server
    cp $IPROOT/coeus/cstat/conf.cstatredis $DATA_DESTDIR/etc/cstat-redis-server.conf
    cp $IPROOT/coeus/cstat/cstat-cli $DATA_DESTDIR/bin/cstat-redis-cli
    chmod 755 $DATA_DESTDIR/bin/cstat-redis-cli
}

install_redis_module() {
    (cd $IPROOT/coeus/redis_modules && gmake clean all && cp *.so $DATA_DESTDIR/lib)
}

install_icap_test() {
    echo creat_icap_test_tool_start
    destdir=$DATA_DESTDIR/bin
    ( cd $IPROOT/coeus/icap_test && gmake || ( fail 1 "Failed to compile icap start-test tool!" ) )
    cp -f $IPROOT/coeus/icap_test/icap_test $destdir || exit 1
    echo creat_icap_test_tool_end
}

install_logcollector() {
    cd $IPROOT/ap/logcollector || fail 1 "Failed to cd to logcollector"
    make || fail 1 "Failed to make the logcollector package"
    install -o root -g wheel -m 0555 $IPROOT/ap/logcollector/cs-borg-dc.py $DATA_DESTDIR/bin || fail 1 "Failed to install cs-borg-dc"
}

install_external_auth() {
    install -d -o root -g wheel -m 0755 $PACKAGE_DIR/data/third_party/external_auth/etc || fail 1 "Failed to make external_auth directory"
    # XXX: I think this is in the wrong location.  It's a non-executable in the bin directory.
    install -o root -g wheel -m 0555 $IPROOT/ap/external_auth/external_auth/external_auth_rpc_server.py $DATA_DESTDIR/bin || fail 1 "Failed to install external_auth_rpc_server.py"
    touch $PACKAGE_DIR/data/third_party/external_auth/etc/radius.seq || fail 1 "Failed to create radius.seq"
}

install_eun_pages() {
    EUN_SRC_ROOT=$IPROOT/coeus/prox/etc/errors_template
    EUN_DST_ROOT=$PACKAGE_DIR/data/db/eun
    CUSTOM_EUN_ROOT=$PACKAGE_DIR/data/pub/configuration/eun
    CUSTOM_CONFIG_ROOT=$PACKAGE_DIR/data/pub/configuration
    for dir in $EUN_SRC_ROOT/*
    do
        lang=`basename $dir`
        if [ -d "$dir" ] && [ "$lang" != "CVS" ]; then
            mkdir -p -m 0775 $EUN_DST_ROOT/${lang} $CUSTOM_EUN_ROOT/${lang}
            cp $EUN_SRC_ROOT/${lang}/ERR_* $EUN_DST_ROOT/${lang}
            cp $EUN_SRC_ROOT/${lang}/ERR_* $CUSTOM_EUN_ROOT/${lang}
        fi
    done
    find $CUSTOM_EUN_ROOT -type f -exec chmod 0664 {} \;
    cd $CUSTOM_CONFIG_ROOT;  tar -zcvf EUN_DEFAULT.tar.gz eun
}

install_coverage_script() {
    echo "Copying coverage script..."
    from=$IPROOT/coeus/tools
    to=$DATA_DESTDIR/bin

    item=coverage_report.sh
    install -o root -g wheel -m 0555 $from/$item $to/$item || fail 1 "Failed to copy $item"
    unset from to
}

install_updater_manifest() {
    from=$IPROOT/coeus/updates
    to=$PACKAGE_DIR/data/db/updater

    install -d -o root -g wheel -m 0755 $to || fail 1 "Failed to create $to"

    echo "Copying client manifest..."
    for updater_file in client_manifest.xml.factory
    do
        install -o root -g wheel -m 0644 $from/$updater_file $to/$updater_file || fail 1 "Failed to copy $updater_file"
    done
    unset from to
}

install_default_password_word_files() {
    # copy password word files

     echo "Copying default password word files..."
     from=$IPROOT/$IPPROD/misc/password_files
     to=$PACKAGE_DIR/data/db/

     for word_file in $password_file
     do
        install -o 1000 -g 1003 -m 0660 $from/$word_file $to/$word_file || fail 1 "Failed to copy word file"
     done


     unset from to
}


install_support_request_data() {
    from=$IPROOT/ap/support_request/support_request
    to=$DATA_DESTDIR/support_request

    install -d -o root -g wheel -m 0755 $to || fail 1 "Failed to create $to"

    echo "Copying Support Request Data"
    for support_file in support_request_data.xml
    do
        install -o root -g wheel -m 0644 $from/$support_file $to/$support_file || fail 1 "Failed to copy $support_file"
    done
    unset from to
}



install_net_snmp() {
    # We need to have autoconf261 installed before compiling net-snmp because
    # PREFIX is used for all dependencies and since perl5 is already installed,
    # the supporting libraries (Locale::gettext) doesn't get placed in the
    # right place.
    srcdir=$IPROOT/$IPPROD/packages/net-snmp
    destdir=$DATA_DESTDIR
    stagedir=${srcdir}/work/stage/${destdir}

    (cd $srcdir; make clean   2>&1)                    || fail 1 "Failed to clean pre'net-snmp'."
    (cd $srcdir; make depends 2>&1)                    || fail 1 "Failed to depends pre 'net-snmp'."
    (cd $srcdir; make clean PREFIX=$destdir 2>&1)      || fail 1 "Failed to clean 'net-snmp'."
    (cd $srcdir; make -DWITH_MFD_REWRITES -DWITH_IPV6 PREFIX=$destdir 2>&1) \
                                                       || fail 1 "Failed to build 'net-snmp'."
    (cd $srcdir; make deinstall PREFIX=$destdir 2>&1)  || fail 1 "Failed to deinstall 'net-snmp.'"
    (cd $srcdir; make install PREFIX=$destdir 2>&1)    || fail 1 "Failed to install 'net-snmp.'"


    # XXX
    # if package system changes, this will have to be fixed
    # We just build the package and pick out the pieces we want

    mkdir -p $destdir/bin
    for fname in snmpget snmpwalk snmptrap
    do
        cp -a $stagedir/bin/$fname $destdir/bin
    done

    mkdir -p $destdir/sbin
    for fname in $stagedir/sbin/*
    do
        cp -a $fname $destdir/sbin
    done

    mkdir -p $destdir/lib
    for fname in $stagedir/lib/lib*
    do
        cp -a $fname $destdir/lib
    done
}

install_adminpassword() {
    echo "Copying adminpassword..."
    from=$IPROOT/coeus/misc/adminpassword
    to=$DATA_DESTDIR/bin

    item=adminpassword.sh
    install -o root -g wheel -m 0555 $from/$item $to/$item || fail 1 "Failed to copy $item"
    unset from to
}

install_jre() {
    # Install jre.
    (
        JAVA_PREFIX=$DATA_DESTDIR/lib/java
        OPENJDK_PKG=openjdk8
        export PACKAGEROOT="https://${CVS_SERVER_NAME}/packages"
        # Opnejdk and its dependencies versions are upgraded in 10.4, Since cs-packages still point to 10.1 ABI , causes issues if we install using pkg install
        ( cd /usr/ports/packages/All && fetch https://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/openjdk8-8.131.11.txz && pkg install openjdk8-8.131.11.txz )
        ( cd /usr/ports/packages/All && fetch https://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/jakarta-commons-daemon-1.0.15.txz && pkg install jakarta-commons-daemon-1.0.15.txz )
        ( cd /usr/ports/packages/All && fetch https://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/tomcat8-8.0.43.txz && pkg install tomcat8-8.0.43.txz )
        ( cd /usr/local && find $OPENJDK_PKG -print | cpio -pdmuv $JAVA_PREFIX )

        ln -s openjdk7 $JAVA_PREFIX/jdk1.6.0

        # trim down to just the JRE
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/bin/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/demo/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/include/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/lib/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/man/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/sample/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/src.zip
    ) || fail 1 "Failed to install the JRE."
}

install_jre_smart_agent() {
    # Install jre for smart agent.
    (
        JAVA_PREFIX=$DATA_DESTDIR/lib/java_smart_agent

        create_dirs $JAVA_PREFIX

        #JAVA_PREFIX=$DATA_DESTDIR/lib/java
        OPENJDK_PKG=openjdk8

        is_jdk_installed=`pkg info | grep ${OPENJDK_PKG}`

        # Note that JDK is also getting installed as part of haystack feature
        # to be on safe side installing here, only if JDK is not already installed
        if [ -z "$is_jdk_installed" ]; then

            pkg install ${OPENJDK_PKG}  || (
                    echo "Unable to install $OPENJDK_PKG"
                    echo "Building $OPENJDK_PKG from source"
                    ( cd /usr/ports/*/${OPENJDK_PKG} \
                                    && make install -DFORCE_PKG_REGISTER ) || exit 1
                    ( cd /usr/ports/*/${OPENJDK_PKG} \
                                    && make $PACKAGE_RECURSIVE -DFORCE_PKG_REGISTER ) || exit 1
            )
        fi

    ( cd /usr/local && find $OPENJDK_PKG -print | cpio -pdmuv $JAVA_PREFIX )


        # trim down to just the JRE
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/bin/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/demo/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/include/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/lib/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/man/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/sample/
        rm -rf $JAVA_PREFIX/$OPENJDK_PKG/src.zip

        install -o root -g wheel -m 0755 $JAVA_PREFIX/$OPENJDK_PKG/jre/bin/java $JAVA_PREFIX/$OPENJDK_PKG/jre/bin/smart_agent || fail 1 "Failed to rename java process to smart_agent process"

    ) || fail 1 "Failed to install the JRE."

}

install_haystack() {
    # Install haystack.
    (cd $IPROOT/ap/reporting/haystack || fail 1 "Failed to cd to haystack."
     ./install_haystack $DATA_DESTDIR/lib $PACKAGE_DIR/data/db || fail 1 "Failed to set up the haystack reporting system."
    ) || fail 1 "Failed to install haystack reporting system."
}

# XXX - This is going to need some help, I have no idea what's going on here.
ANNIHILATOR_FILES="defaults.conf logger.conf test.py"
install_testing_binaries() {
    # Create an annihilator directory and copy in ironport.db, ironport.shared
    # and a few of the non-python files that Annihilator needs to run.
    # Finally, tar up this directory.

    echo ""
    echo "Installing testing binaries..."

    dest_dir=$PACKAGE_DIR/annihilator
    echo "Destdir: $dest_dir"
    mkdir -p $dest_dir
    mkdir -p $dest_dir/libexec

    for file in $ANNIHILATOR_FILES; do
        cp $IPROOT/coeus/annihilator/$file $dest_dir
    done

    # This 'annihilator' is a .sh bootstrap script
    # keep out of ANNIHILATOR_FILES so we can do something special at pkg_create
    cp $IPROOT/coeus/annihilator/annihilator $dest_dir

    # This 'annihilator' in libexec is really bootstrap.py
    link_or_copy_or_fail 0 0 0555 BOOTSTRAP $dest_dir/libexec/annihilator

    echo "Done with testing binaries."

}


install_global_configuration() {
    # copy global configuration file into etc directory
    install -o root -g wheel -m 0644 $IPROOT/coeus/release/asyncos.conf $PACKAGE_DIR/etc || fail 1 "Failed to copy asyncos.conf"
    echo "BUILD_DATE=\"$BUILD_DATE\"" >> $PACKAGE_DIR/etc/asyncos.conf || fail 1 "Failed to modify asyncos.conf"
    echo "RELEASE_TAG=$as_tag"    >> $PACKAGE_DIR/etc/asyncos.conf || fail 1 "Failed to modify asyncos.conf"
}

install_version_file() {
    echo "$IPPROD $MAJOR_NUMBER.$MINOR_NUMBER.$SUBMINOR_NUMBER-$BUILD" > $DATA_DESTDIR/VERSION || fail 1 "Failed to make VERSION file"
}

install_counters() {
    (
        cd $IPROOT
        install -d -o root -g wheel -m 0755 $PACKAGE_DIR/data/db/reporting/counters/current/ || fail 1 "Failed to create counters dir."
        install -d -o root -g wheel -m 0755 $DATA_DESTDIR/counters/ || fail 1 "Failed to create counters dir."
        for pathname in `cat $IPROOT/coeus/release/counter_manifest`
        do
            install -o root -g wheel -m 0644 $pathname $DATA_DESTDIR/counters/ || fail 1 "Failed to copy counter file $pathname."
                        file=`basename $pathname`
                        ln -s $IPDATA/release/current/counters/$file $PACKAGE_DIR/data/db/reporting/counters/current/ || fail 1 "Failed to link counter file $pathname."
        done
    ) || fail 1 "Failed to install counter files."
}

install_counterd_conf() {
    install -o root -g wheel -m 0644 $IPROOT/ap/reporting/heimdall/counterd_release.conf $DATA_DESTDIR/etc/counterd.conf || fail 1 "Failed to copy counterd.conf file"
}

make_packages() {
    echo ""
    echo "Making packages..."

    if [ "x$phoebe_binaries" = "x1" ]
    then

        echo "Pruning package compiled python files..."
        find $PACKAGE_DIR -name "*.pyc" -delete
        find $PACKAGE_DIR -name "*.pyo" -delete

        if [ "x$sandbox_mode" != "x1" ]
        then
            echo "--> Remove write executable stack"
            #( cd $PACKAGE_DIR &&
              #execstack -c $DATA_DESTDIR/lib/python2.6_11_amd64_nothr/lib-dynload/_ctypes.so
            #) || fail 1 "Failed to remove write executable stack"
        fi

        echo "--> $PACKAGE_NAME.tgz"
        ( cd $PACKAGE_DIR &&
          tar -czvf $IPROOT/$IPPROD/release/$PACKAGE_NAME.tgz *
        ) || fail 1 "Failed to create $PACKAGE_NAME.tgz"

        # Tar up the debug ipoe files
        echo "--> debug_ipoe-$PACKAGE_NAME.tgz"
        ( cd $DEBUG_EGG_DESTDIR &&
          tar -czvf $IPROOT/$IPPROD/release/debug_ipoe-$PACKAGE_NAME.tgz .
        ) || fail 1 "Failed to create debug_ipoe_files.tgz"
    fi

    if [ "x$testing_binaries" = "x1" ]
    then
        ANNIHILATOR_PACKAGE_NAME=`echo "$PACKAGE_NAME" | sed -e 's/^[a-z]*-//;s/^/annihilator-/'`
        dest_dir=$PACKAGE_DIR/annihilator
        TMP_PLIST_FILE=/tmp/app_build_plist.$$
        TMP_PKG_COMMENT=/tmp/app_build_comment.$$
        TMP_PKG_DESCRIPTION=/tmp/app_build_description.$$
        (
            cd $PACKAGE_DIR
            echo "@owner root"
            echo "@group wheel"
            echo "@mode 755"
            echo "annihilator/libexec/annihilator"
            echo "annihilator/annihilator"

        ) > $TMP_PLIST_FILE

        echo "Annihilator" > $TMP_PKG_COMMENT
        echo "Annihilator" > $TMP_PKG_DESCRIPTION

        echo "--> $ANNIHILATOR_PACKAGE_NAME.tgz"
        pkg_create -p /usr/local -s $PACKAGE_DIR -c $TMP_PKG_COMMENT -d $TMP_PKG_DESCRIPTION -f $TMP_PLIST_FILE $ANNIHILATOR_PACKAGE_NAME.tgz

        rm $TMP_PKG_COMMENT
        rm $TMP_PKG_DESCRIPTION
        rm $TMP_PLIST_FILE
    fi

}

install_key_generator() {
    echo "Creating crypto-keygen"
    ( cd $IPROOT/coeus/prox/keygen && gmake -j4 ) \
    || fail 1 "Failed to create crypto-keygen"

    install -o root -g wheel -m 0755 $IPROOT/coeus/prox/keygen/crypto-keygen $DATA_DESTDIR/bin/crypto-keygen || fail 1 "Failed to copy crypto-keygen"
}

create_beaker_monitor() {
    echo "Creating beaker-monitor"
    ( cd $IPROOT/coeus/beaker/monitor && make -j4 ) \
    || fail 1 "Failed to create beaker-monitor"

    install -o root -g wheel -m 0755 $IPROOT/coeus/beaker/monitor/beaker_monitor $DATA_DESTDIR/bin/beaker_monitor || fail 1 "Failed to copy beaker-monitor"
}


install_beaker_updater() {
    echo "installing beaker-updater"
    ( cd $IPROOT/coeus/beaker/updater && make -j4 ) \
    || fail 1 "Failed to create beaker-updater"
    install -o root -g wheel -m 0755 $IPROOT/coeus/beaker/updater/libbeaker_updater.so $DATA_DESTDIR/lib/ || fail 1 "Failed to install libbeaker_updater.so"
    install -o root -g wheel -m 0755 $IPROOT/coeus/beaker/updater/beaker_updater.so $DATA_DESTDIR/lib/ || fail 1 "Failed to install beaker_updater.so"
}


copy_certificates() {
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/db/sslcert || fail 1 "Failed to create sslcert dir"
    install -o root -g wheel -m 0644 $IPROOT/coeus/coroutine/coro_ssl_data/demo-cert.txt $PACKAGE_DIR/data/db/sslcert/factory.crt.pem || fail 1 "Failed to install secure auth cert."
    install -o root -g wheel -m 0644 $IPROOT/coeus/coroutine/coro_ssl_data/demo-key.txt $PACKAGE_DIR/data/db/sslcert/factory.key.pem || fail 1 "Failed to install secure auth key."
    install -d -o root -g 1003 -m 0775 $PACKAGE_DIR/data/coroutine/coro_ssl_data || fail 1 "Failed to create coro_ssl_data dir"
    install -o root -g wheel -m 0644 $IPROOT/coeus/coroutine/coro_ssl_data/demo-cert.txt $PACKAGE_DIR/data/coroutine/coro_ssl_data/demo-cert.txt || fail 1 "Failed to install demo-cert.txt"
    install -o root -g wheel -m 0644 $IPROOT/coeus/coroutine/coro_ssl_data/demo-key.txt $PACKAGE_DIR/data/coroutine/coro_ssl_data/demo-key.txt || fail 1 "Failed to install demo-key.txt"
    install -o root -g wheel -m 0644 $IPROOT/coeus/coroutine/coro_ssl_data/dh_2048.txt $PACKAGE_DIR/data/coroutine/coro_ssl_data/dh_2048.txt || fail 1 "Failed to install dh_2048.txt"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/db/certd || fail 1 "Failed to create certd dir"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/db/sicapcerts  || fail 1 "Failed to create sicapcert dir"
    install -o root -g wheel -m 0644 $IPROOT/coeus/coroutine/coro_ssl_data/sign_untrusted.crt.txt $PACKAGE_DIR/data/db/sslcert/sign_untrusted.crt.pem || fail 1 "Failed to install sign_untrusted.crt.pem"
    install -o root -g wheel -m 0644 $IPROOT/coeus/coroutine/coro_ssl_data/sign_untrusted.key.txt $PACKAGE_DIR/data/db/sslcert/sign_untrusted.key.pem || fail 1 "Failed to install sign_untrusted.key.pem"
}

install_trusted_ca_file() {
    install -o root -g wheel -m 0644 $IPROOT/coeus/share/trustedca.pem $DATA_DESTDIR/share/trustedca.pem || fail 1 "Failed to copy trusted CA file"
    if [ "x$sandbox_mode" != "x1" ]
    then
        install -o root -g wheel -m 0644 $IPROOT/ap/trusted_root_certs/files/trustedca.pickle $DATA_DESTDIR/share/trustedca.pickle || fail 1 "Failed to copy trusted CA pickle file"
        install -o root -g wheel -m 0644 $IPROOT/ap/trusted_root_certs/files/trustedca.pem.download $DATA_DESTDIR/share/trustedca.pem.download || fail 1 "Failed to copy updater base trusted CA file"
        install -o root -g wheel -m 0644 $IPROOT/ap/trusted_root_certs/files/cert_blacklist $DATA_DESTDIR/share/cert_blacklist || fail 1 "Failed to copy blacklist file"
    fi # !sandbox
}

install_unbound_root_key(){
    echo "Copying unbound root keys"

    from=$IPROOT/$IPPROD/dns
    to=$DATA_DESTDIR/dnskey

    install -o root -g wheel -m 0644 $from/dns_root.key $to/dns_root.key || fail 1 "Failed to copy dns_root.key"

    unset from to

}

install_updater_bundle_file() {
        install -o root -g wheel -m 0644 $IPROOT/$IPPROD/share/trustedca.pem $DATA_DESTDIR/share/updater_bundle.pem || fail 1 "Failed to copy updater bundle file"
}


install_internal_ca_file() {
    if [ "x$sandbox_mode" != "x1" ]
    then
        install -o root -g wheel -m 0644 $IPROOT/ap/internal_resources/files/internal_ca.pem $DATA_DESTDIR/share/internal_ca.pem || fail 1 "Failed to copy updater base internal CA file"
    fi # !sandbox
}

install_updater_bundle_file() {
        install -o root -g wheel -m 0644 $IPROOT/$IPPROD/share/trustedca.pem $DATA_DESTDIR/share/updater_bundle.pem || fail 1 "Failed to copy updater bundle file"
}

install_openssl_cnf_file() {
    install -o root -g wheel -m 0644 $IPROOT/coeus/share/openssl.cnf $DATA_DESTDIR/share/openssl.cnf || fail 1 "Failed to copy openssl.cnf file"
    mkdir -p $PACKAGE_DIR/usr/local/openssl || fail 1 "Failed to make openssl directory"
    ln -sf $IPDATA/share/openssl.cnf $PACKAGE_DIR/usr/local/openssl/openssl.cnf || fail 1 "Failed l
ink to openssl conf"
}

install_comodo_crl_file() {
    install -o root -g wheel -m 0644 $IPROOT/coeus/share/UTN-USERFirst-Hardware.crl $DATA_DESTDIR/share/UTN-USERFirst-Hardware.crl || fail 1 "Failed to copy Comodo CRL file"
}

install_clamav () {
    # Copy library files
    #cp /usr/local/lib/libjson.so* $DATA_DESTDIR/lib/ || fail 1  "Failed to copy clamav libs"
    cp /usr/local/lib/libjson-c.so* $DATA_DESTDIR/lib/ || fail 1  "Failed to copy clamav libs"
    cp /usr/local/lib/libbz2.so* $DATA_DESTDIR/lib/ || fail 1  "Failed to copy bzip2 libs"
    cp /usr/local/lib/libpcre2-* $DATA_DESTDIR/lib/ || fail 1  "Failed to copy pcre2 libs"
    cp /usr/local/lib/libclamav.so* $PACKAGE_DIR/data/fire_amp/lib/ || fail 1  "Failed to copy clamav libs"
    cp /usr/local/lib/libclammspack.so* $PACKAGE_DIR/data/fire_amp/lib/ || fail 1  "Failed to copy clammspack libs"
}

copy_kdump_dependent_libs() {
    cp /master/lib/casper/libcap_grp.so.0 $DATA_DESTDIR/lib/ || fail 1  "Failed to copy libcap_grp.so.0"
    cp /master/lib/casper/libcap_pwd.so.0 $DATA_DESTDIR/lib/ || fail 1  "Failed to copy libcap_pwd.so.0"
}

copy_libs () {
    for file in \
      lib/libc.so.* \
      lib/libthr.so.* \
      lib/libcrypto.so.* \
      lib/libcrypt.so.* \
      lib/libedit.so.* \
      lib/libkvm.so.* \
      lib/libm.so.* \
      lib/libmalloc.so.* \
      lib/libmd.so.* \
      lib/libncurses.so.* \
      lib/libutil.so.* \
      lib/libz.so.* \
      usr/lib/libbz2.so.* \
      usr/lib/libmagic.so.* \
      usr/lib/libpam.so.* \
      usr/lib/libssl.so.* \
      usr/lib/libstdc++.so.* \
      /usr/local/lib/libglib-2.0.so.* \
      /usr/local/lib/libgobject-2.0.so.* \
      /usr/local/lib/libiconv.so.* \
      /usr/local/lib/libintl.so.* \
      /usr/local/lib/libltdl.so.* \
      /usr/local/lib/libpcre.so.* \
      /usr/local/lib/libxml2.so.* \
      /usr/local/lib/libxmlsec1-openssl.so.* \
      /usr/local/lib/libxmlsec1.so.* \
      /usr/local/lib/libxslt.so.* \
      /usr/local/lib/libxmlsec1-openssl.la \
      /usr/local/lib/libxmlsec1-openssl.a \
      /usr/local/lib/libxmlsec1.la \
      /usr/local/lib/libssl.so.* \
      /usr/local/lib/libcrypto.so.* \
      ;
    do
        # TODO : This is a temporary fix, Need to refine it.
        echo "$file" | grep -q "libstdc"
        if [ $? -eq 0 ] && [ "x$type" = "xfreebsd_10_amd64_build" ]
        then
            echo "Skipping copy for $file"
        else
            cp $IPROOT/freebsd/mods/build/$file $DATA_DESTDIR/lib/ || \
            ([ ! -h /$file ] && cp /data/$file $DATA_DESTDIR/lib/) || \
            cp /$file $DATA_DESTDIR/lib/ || \
            cp /master/$file $DATA_DESTDIR/lib/ || \
            exit 1
        fi
    done || fail 1 "Copy libs"
}

copy_config () {
    for CONFIG_DIR in `cat CONFIG_DIRS`
    do
        $IPDATA/bin/python $IPROOT/coeus/release/setup_config.py \
            --translation-manifest=$IPROOT/coeus/release/TRANSLATION_MANIFEST \
            none $IPROOT/$CONFIG_DIR $PACKAGE_DIR/data/db/config || fail 1 "Failed to setup config"
    done

    install -o root -g wheel -m 0644 $IPROOT/coeus/release/TRANSLATION_MANIFEST $DATA_DESTDIR/etc/ || fail 1 "Failed to copy TRANSLATION_MANIFEST"
}

install_install_modes() {
    install -d -o root -g wheel -m 0755 $DATA_DESTDIR/etc/install_modes/
    for file in $IPROOT/coeus/release/install_modes/*
    do
        case "$file" in
        $IPROOT/coeus/release/install_modes/README)
            # Skip the README file.
            ;;
        *)
            install -o root -g wheel -m 0644 $file $DATA_DESTDIR/etc/install_modes/
            ;;
        esac
    done
}

install_nginx() {
    NGINX_SRC_DIR=$IPROOT/$IPPROD/packages/nginx
    NGINX_PREFIX=$PACKAGE_DIR/data/third_party/nginx
    cd $NGINX_SRC_DIR
    mkdir -p $NGINX_PREFIX/etc/conf
    mkdir -p $NGINX_PREFIX/etc/certs
    mkdir -p $NGINX_PREFIX/etc/logs
    mkdir -p $NGINX_PREFIX/run
    mkdir -p $NGINX_PREFIX/tmp/nginx
    make clean deinstall reinstall DEFAULT_VERSIONS=ssl=ciscossl BATCH=yes PREFIX=$NGINX_PREFIX NGINX_VARDIR=/data/third_party/nginx NGINX_ACCESSLOG=/data/third_party/nginx/etc/logs/access_log NGINX_ERRORLOG=/data/third_party/nginx/etc/logs/error_log || fail 1 "Failed to install 'NGINX'"
    echo " NGINX installation complete. Applying the default config..."
    touch $NGINX_PREFIX/etc/certs/cert.key
    touch $NGINX_PREFIX/etc/certs/cert.pem
    install -o root -g wheel -m 0640 $IPROOT/third_party/nginx/nginx.conf $NGINX_PREFIX/etc/nginx/
    install -o root -g wheel -m 0755 $IPROOT/third_party/nginx/nginx.conf_no_tg.tmpl $NGINX_PREFIX/etc/nginx/
    install -o root -g wheel -m 0755 $IPROOT/third_party/nginx/nginx.conf.tmpl $NGINX_PREFIX/etc/nginx/
    rm -f /etc/rc.d/nginx
    ln -s $NGINX_PREFIX/etc/rc.d/nginx /etc/rc.d/nginx

    #Hardening the security
    chmod 510 $NGINX_PREFIX/sbin/nginx
    chmod 700 $NGINX_PREFIX/etc/nginx
    chmod 700 $NGINX_PREFIX/run

    echo "NGINX is ready for use..."
  }

create_directories() {
    # Groups:
    # 1000 - admin
    # 1001 - operators
    # 1002 - guest
    # 1003 - config
    # 1004 - log
    for dir in $DATA_DESTDIR \
               $DATA_DESTDIR/bin \
               $DATA_DESTDIR/etc \
               $DATA_DESTDIR/etc/samba \
               $DATA_DESTDIR/lib \
               $DATA_DESTDIR/libexec \
               $DATA_DESTDIR/share \
               $DATA_DESTDIR/web \
               $DATA_DESTDIR/dnskey \
               $PACKAGE_DIR/data/cores \
               $PACKAGE_DIR/data/db \
               $PACKAGE_DIR/data/db/config \
               $PACKAGE_DIR/data/db/eun \
               $PACKAGE_DIR/data/db/hermes \
               $PACKAGE_DIR/data/db/local_authd \
               $PACKAGE_DIR/data/home \
               $PACKAGE_DIR/data/log \
               $PACKAGE_DIR/data/log/stdout \
               $PACKAGE_DIR/data/log/samba \
               $PACKAGE_DIR/data/third_party \
               $PACKAGE_DIR/data/third_party/connector \
               $PACKAGE_DIR/etc \
               $PACKAGE_DIR/usr \
               $PACKAGE_DIR/usr/local \
               $PACKAGE_DIR/usr/local/etc \
               $PACKAGE_DIR/var \
               $PACKAGE_DIR/var/db \
               $PACKAGE_DIR/var/db/godspeed \
               $PACKAGE_DIR/var/tmp/nginx
    do
        install -d -o root -g wheel -m 0755 $dir || fail 1 "Failed to create $dir"
    done

    install -d -o root -g 1000 -m 0777 $PACKAGE_DIR/data/db/rollback || fail 1 "Failed to create rollback"
    install -d -o root -g 1004 -m 0775 $PACKAGE_DIR/data/pub || fail 1 "Failed to create pub"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/pub/configuration || fail 1 "Failed to create config dir"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/pub/configuration/iccm || fail 1 "Failed to create iccm"
    install -d -o root -g 1003 -m 0775 $PACKAGE_DIR/data/pub/configuration/eun || fail 1 "Failed to create custom eun dir"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/pub/captures || fail 1 "Failed to create captures dir"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/pub/diagnostic || fail 1 "Failed to create diagnostic dir"
    install -d -o root -g wheel -m 1777 $PACKAGE_DIR/data/tmp || fail 1 "Failed to create tmp"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/coverage || fail 1 "Failed to create coverage"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/db/certd || fail 1 "Failed to create certd dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/certd/saml20 || fail 1 "Failed to create saml dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/forests || fail 1 "Failed to create forests dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/certd/saml20/idp_cert_store || fail 1 "Failed to create idp certd dir"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/db/sslcert || fail 1 "Failed to create sslcert dir"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/data/db/fips || fail 1 "Failed to create fips dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/radius || fail 1 "Failed to create radius dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/saml20 || fail 1 "Failed to create saml dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/saml20/idp_dir || fail 1 "Failed to create idp metadata dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/saved_configs || fail 1 "Failed to create saved_configs dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/vals || fail 1 "Failed to create vals dir"
    install -d -o root -g 1003 -m 0777 $PACKAGE_DIR/data/db/license || fail 1 "Failed to create license dir"
    install -d -o root -g 1003 -m 4777 $PACKAGE_DIR/data/python-eggs || fail 1 "Failed to create eggs dir"
    install -d -o root -g 1003 -m 0770 $PACKAGE_DIR/var/db/godspeed/features || fail 1 "Failed to features backup dir"
    install -d -o root -g 1003 -m 0775 $PACKAGE_DIR/usr/share/zoneinfo_tmp_dir || fail 1 "Failed to create zoneinfo dir"

    # XXX: I don't like the permissions on features, it really should be group writeable only.
    # XXX: Double note: stage/etc/rc will chown -R the features directory to admin.  Don't know why.
    install -d -o root -g wheel -m 0777 $PACKAGE_DIR/data/db/features || fail 1 "Failed to create features"
    install -d -o root -g wheel -m 0777 $PACKAGE_DIR/data/db/hybrid_data || fail 1 "Failed to create hybrid_data"
    install -d -o root -g wheel -m 0777 $PACKAGE_DIR/data/db/sse_connector_data || fail 1 "Failed to create sse_connector_data"
}

create_symlinks() {
    for path in $DATA_DESTDIR/*
    do
        file=`basename $path`
        ln -s release/current/$file $PACKAGE_DIR/data/ || fail 1 "Failed to create $file symlink."
    done
}

echo "################################## "
echo "# Setup directories for cs-borg-data-collection # "
echo "################################## "

install_cs-borg-dc () {
        srcdir=$IPROOT/coeus/third_party/cs-borg-data-collection/cs-borg-dc
        cp -r $srcdir $DATA_DESTDIR/lib || fail 1 "Failed to copy files from $srcdir."
}

# XXX - This will NOT work as it stands (pycbox_main has been removed).
build_firestone() {
    ICU_DIR=$IPROOT/third_party/icu4c/source
    FIRESTONE_DIR=$IPROOT/firestone/ca
    PYTHONROOT="/usr/local"
    PYTHON="$PYTHONROOT/bin/python"
    PYTHON_VER=`$PYTHON -c "import distutils.sysconfig;print distutils.sysconfig.get_python_version()"`
    PYTHON_LIB_DIR="$PYTHONROOT/lib/python${PYTHON_VER}"

    # KEEP THIS IN SYNC WITH coeus/build_firestone.db!!!
    PYCBOX_INCLUDE="$PYTHON_LIB_DIR/ ./$IPPROD/rpc ./scanners ./firestone ./$IPPROD/godlib/bencode.py"
    PYCBOX_EXCLUDE="*/CVS,*/test,*/tests,*/examples,*/test.py,*/doc,*/docs,*/setup.py,*/frozen,*/frozen_lib,*/build,*/backup"
    PYTHONPATH=`$PYTHON $IPROOT/$IPPROD/python_path.py $IPROOT`

    # Build the firestone SDK into an so.
    (cd $ICU_DIR && ([ -f ./Makefile ] || ./configure --enable-static) && gmake -j4 install) || exit 1
    (cd $FIRESTONE_DIR && ([ -f ./ca.so ] || gmake -j4 )) || exit 1

    # Freeze pycbox_main.
    (cd $IPROOT/firestone; $PYTHON $IPROOT/third_party/python/Tools/freeze/freeze.py -d -r _xmlplus=xml -x site -x _warnings -o frozen -p $PYTHONROOT $IPROOT/$IPPROD/pycbox/pycbox_main.py 2>&1) || fail 1 "Failed to freeze python source."
    (cd $IPROOT/firestone/frozen &&  gmake -j4 2>&1) || fail 1 "Failed to create frozen binaries."

    # Create the firestone pycbox.
    (cd $IPROOT && $IPDATA/bin/python -OO $IPROOT/$IPPROD/pycbox/pycbox_build.py --force --verbose --exclude=$PYCBOX_EXCLUDE firestone $PYCBOX_INCLUDE) || fail 1 "Failed to build pycbox"

    # Install the firestone pycbox.
    install -d -o root -g wheel -m 0755 $DATA_DESTDIR/lib/pycbox/
    install -o root -g wheel -m 0644 $IPROOT/firestone.db $DATA_DESTDIR/lib/pycbox/ || fail 1 "Failed to install code database"

    # Create firestone.shared.
    install -d -o root -g wheel -m 0755 $DATA_DESTDIR/lib/pycbox/firestone.shared

    install $PYTHON_LIB_DIR/lib-dynload/*.so $DATA_DESTDIR/lib/pycbox/firestone.shared || fail 1 "Failed to copy shared modules."
    install $PYTHON_LIB_DIR/site-packages/*.so $DATA_DESTDIR/lib/pycbox/firestone.shared || fail 1 "Failed to copy so"
    install $FIRESTONE_DIR/ca.so $DATA_DESTDIR/lib/pycbox/firestone.shared || fail 1 "Failed to copy firestone so."
    install $IPROOT/$IPPROD/python_modules/*.so $DATA_DESTDIR/lib/pycbox/firestone.shared || fail 1 "Failed to copy $IPPROD python modules."

    # Install binaries.
    PYCBOX=$IPROOT/firestone/frozen/pycbox_main
    install -d -o root -g wheel -m 0755 $DATA_DESTDIR/bin || fail 1 "Couldn't install the frozen binary"
    link_or_copy_or_fail 0 0 0555 PYCBOX $DATA_DESTDIR/bin/firestone_rpc_server

    # Install Firestone .sse
    install -d -o root -g wheel -m 0755 $DATA_DESTDIR/etc/firestone || fail 1 "Couldn't create firestone directory."
    install $IPROOT/firestone/firestone.sse $DATA_DESTDIR/etc/firestone || fail 1 "Couldn't install firestone.sse"

    # Install a version file
    echo "$as_tag" > $DATA_DESTDIR/etc/firestone/VERSION || fail 1 "Couldn't output VERSION file"

    # Tar everything up.
    (cd $DATA_DESTDIR && tar -cvzf $IPROOT/$IPPROD/release/$as_tag.tgz *) || fail 1 "Couldn't create tar"
}

build_lasso_depends() {
 (package_build /usr/ports/devel/p5-Locale-gettext) || fail 1 "p5-Locale-gettext installation failed while building lasso"
 (package_build /usr/ports/misc/help2man) || fail 1 "help2man installation failed while building lasso"
 (package_build /usr/ports/devel/autoconf-wrapper) || fail 1 "autoconf-wrapper installation failed while building lasso"
 (package_build /usr/ports/devel/automake-wrapper) || fail 1 "automake-wrapper installation failed while building lasso"
 (package_build /usr/ports/devel/m4) || fail 1 "m4 installation failed while building lasso"
 if [ "x$type" = "xfreebsd_10_amd64_build" ]
 then
   (package_build /usr/ports/devel/autoconf) || fail 1 "autoconf261 installation failed while building lasso"
   (package_build /usr/ports/devel/automake) || fail 1 "automake 1.10 installation failed while building lasso"
 else
   (package_build /usr/ports/devel/autoconf) || fail 1 "autoconf installation failed while building lasso"
   (package_build /usr/ports/devel/automake) || fail 1 "automake installation failed while building lasso"
 fi
 (package_build /usr/ports/devel/automake) || fail 1 "automake 1.10 installation failed while building lasso"
 # We need a newer version of libxml2 than what is in /usr/ports
 (
  # xmlsec has broken $PACKAGE_RECURSIVE target, as a consequence have to explicitly build
  # its dependencies.  As you will see prereqs for xmlsec vary depending on target os
  #Latest version of libxml2 doesnot build in FreeBSD6 chroot
  if [ `uname -r | sed 's/\..*$//'` -lt 9 ]
  then
     if [ "x$type" = "xfreebsd_6_i386_build" ]
     then
         package_build $IPROOT/coeus/packages/libxml2
     else
         package_build /usr/ports/textproc/libxml2
     fi
  fi &&
  if [ "x$type" = "xfreebsd_6_i386_build" ]
  then
    package_build /usr/ports/devel/libtool15
    package_build /usr/ports/devel/libltdl15
  else
    package_build /usr/ports/devel/libltdl
  fi &&
  if [ "x$type" = "xfreebsd_6_i386_build" ]
  then
    package_build $IPROOT/coeus/packages/libxslt &&
    package_build /usr/ports/security/xmlsec1
  elif [ "x$type" = "xfreebsd_10_amd64_build" ]
  then
    package_build $IPROOT/coeus/packages/libxslt &&
    package_build /usr/ports/security/libgcrypt &&
    package_build /usr/ports/security/xmlsec1
  else
    package_build /usr/ports/print/indexinfo &&
    package_build /usr/ports/converters/libiconv &&
    package_build /usr/ports/devel/gettext-runtime &&
    package_build /usr/ports/devel/ncurses &&
    package_build  /usr/ports/devel/gettext &&
    package_build /usr/ports/security/libgpg-error &&
    package_build /usr/ports/lang/perl5.32  &&
    package_build $IPROOT/coeus/packages/gdbm-1.13_1 && cd $IPROOT/coeus/packages/gdbm-1.13_1 && pkg create gdbm-1.13_1 && mkdir -p work/pkg && cp gdbm*.txz work/pkg && cp gdbm*.txz /usr/ports/packages/All/ &&
    package_build /usr/ports/security/libgcrypt &&
    package_build /usr/ports/textproc/libxslt &&
    package_build /usr/ports/security/xmlsec1 &&
    package_build /usr/ports/devel/pkgconf && cd /usr/ports/devel/pkgconf && pkg create pkgconf && mkdir -p work/pkg &&
    cp pkgconf-*.txz work/pkg && cp pkgconf-*.txz /usr/ports/packages/All/ &&
    package_build /usr/ports/devel/libffi && cd /usr/ports/devel/libffi && pkg create libffi && mkdir -p work/pkg &&
    cp libffi-*.txz work/pkg &&
    package_build /usr/ports/devel/libltdl && cd /usr/ports/devel/libltdl && pkg create libltdl && mkdir -p work/pkg &&
    cp libltdl-*.txz work/pkg
  fi
 ) || fail 1 "xmlsec1 installation failed while building lasso"
 (package_build /usr/ports/devel/pcre) || fail 1 "pcre installation failed while building lasso"
 uname -a
 if [ `uname -r | sed 's/\..*$//'` -lt 10 ]
 then
   (package_build $IPROOT/coeus/packages/glib20.old) || fail 1 "glib20 installation failed while building lasso"
 else
   (package_build $IPROOT/coeus/packages/glib20) || fail 1 "glib20 installation failed while building lasso"
 fi
}

install_ytc_files(){

#create folder and copy engine files
mkdir -p $PACKAGE_DIR/data/db/ytc
cp $IPROOT/coeus/ytc/ytc.py $PACKAGE_DIR/data/db/ytc/
cp $IPROOT/coeus/ytc/ytc_rpc_server.py $PACKAGE_DIR/data/db/ytc/
cp $IPROOT/coeus/ytc/ytc_util.py $PACKAGE_DIR/data/db/ytc/
cp $IPROOT/coeus/ytc/ytc_cat_api.py $PACKAGE_DIR/data/db/ytc/
cp $IPROOT/coeus/ytc/ytc_platform_connector.py $PACKAGE_DIR/data/db/ytc/
cp $IPROOT/coeus/ytc/ytc_fast_rpc_blocking_threadsafe.py $PACKAGE_DIR/data/db/ytc/
cp $IPROOT/coeus/ytc/ytc_fast_rpc_proxy.py $PACKAGE_DIR/data/db/ytc/
cp $IPROOT/coeus/ytc/ttldict.py $PACKAGE_DIR/data/db/ytc/

#create a hard link for ytc to python2.7
ln -f  /usr/local/bin/python2.7 $PACKAGE_DIR/usr/local/bin/ytc

#google api
fetch https://engci-maven.cisco.com/artifactory/contentsecurity-thirdparty/packages/py27-google-api-python-client-1.7.6.txz
tar -xvf py27-google-api-python-client-1.7.6.txz
cp -r usr/local/lib/python2.7/site-packages/googleapiclient $PACKAGE_DIR/data/db/ytc/

#missing file
cp /usr/local/lib/python2.7/site-packages/pkg_resources/_vendor/six.py $PACKAGE_DIR/data/db/ytc/

#httplib2
fetch https://engci-maven.cisco.com/artifactory/contentsecurity-thirdparty/packages/httplib2-0.13.1.2.tar.gz
tar -xvf httplib2-0.13.1.2.tar.gz
cd httplib2-0.13.1
python2.7 setup.py build_ext --inplace
cp -r python2/httplib2 $PACKAGE_DIR/data/db/ytc/

#uritemplate
fetch https://engci-maven.cisco.com/artifactory/contentsecurity-thirdparty/packages/uritemplate-3.0.0.tar.gz
tar -xvf uritemplate-3.0.0.tar.gz
cd uritemplate-3.0.0
python2.7 setup.py build_ext --inplace
cp -r uritemplate $PACKAGE_DIR/data/db/ytc/

}

install_adc_engine(){
    echo "######################"
    echo "Installing ADC Engine"
    echo "######################"
    echo "Starting `date` adc build"
    ADC_ENGINE_INSTALL_PATH=$PACKAGE_DIR/data/third_party/adc
    ADC_JSON_INSTALL_PATH=$PACKAGE_DIR/data/db/adc
    mkdir -p $ADC_ENGINE_INSTALL_PATH
    mkdir -p $ADC_JSON_INSTALL_PATH
    cp $IPROOT/coeus/adc/adc/adc_*.py $ADC_ENGINE_INSTALL_PATH
    cp $IPROOT/coeus/adc/CASI/adc.json $ADC_JSON_INSTALL_PATH

    #create a hard link for adc to python
    ln -f  /usr/local/bin/python $PACKAGE_DIR/usr/local/bin/adc

    echo "Copying ADC SSE config"
    install -o root -g wheel -m 0644 $IPROOT/coeus/adc/adc.sse $ADC_ENGINE_INSTALL_PATH || fail 1 "Failed to copy adc.sse"
    echo "Ending `date` ADC Engine installation"
}

install_umbrella_client(){
    echo "###########################"
    echo "Installing Umbrella Client"
    echo "###########################"
    echo "Installing `date` umbrella_client"
    #create folder and copy engine files
    mkdir -p $PACKAGE_DIR/data/umbrella_client
    cp $IPROOT/coeus/umbrella_client/config_updater.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy umbrella_client/config_updater.py"
    cp $IPROOT/coeus/umbrella_client/config_api.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy umbrella_client/config_api.py"
    cp $IPROOT/coeus/umbrella_client/constants.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy umbrella_client/constants.py"
    cp $IPROOT/coeus/umbrella_client/umbrella_client.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy umbrella_client/umbrella_client.py"
    cp $IPROOT/coeus/umbrella_client/hybrid_regis_api.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy umbrella_client/hybrid_regis_api.py"
    cp $IPROOT/scanners/picklelog_client.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy scanners/picklelog_client.py"
    cp $IPROOT/coeus/umbrella_client/umbrella_logger.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy umbrella_client/umbrella_logger.py"
    cp $IPROOT/coeus/umbrella_client/realm_util.py $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy umbrella_client/realm_util.py"

    #create a hard link for umbrella client to python2.7
    ln -f /usr/local/bin/python2.7 $PACKAGE_DIR/usr/local/bin/umbrella_client

    #Copy websocket libraries
    cp -r /usr/local/lib/python2.7/site-packages/websocket $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy websocket module"
    cp -r /usr/local/lib/python2.7/site-packages/websocket_client-0.59.0.dist-info $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy websocket_client module"
    cp -r /usr/local/lib/python2.7/site-packages/yaml $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy yaml module"
    cp -r /usr/local/lib/python2.7/site-packages/jwt $PACKAGE_DIR/data/umbrella_client/ \
    || fail 1 "Failed to copy jwt module"

    #Copy conf file, the ususal flow of installing the conf file is failing, thus, doing the copy operation here.
    cp $IPROOT/coeus/umbrella_client/heimdall/umbrella_client/umbrella_client_release.conf $DATA_DESTDIR/etc/heimdall/umbrella_client.conf \
    || fail 1 "Failed to copy umbrella_client.conf file"

    echo "Ending `date` umbrella client installation"
}

install_report_shipper_client(){
    echo "##############################################"
    echo "Installing SWA Hybrid Reporting Client"
    echo "##############################################"
    echo "Installing `date` report_shipper_client"
    #create folder and copy engine files
    mkdir -p $PACKAGE_DIR/data/swa_hybrid_reporting
    cp $IPROOT/coeus/swa_hybrid_reporting/report_shipper_client.py $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy swa_hybrid_reporting/report_shipper_client.py"
    cp $IPROOT/coeus/swa_hybrid_reporting/reporting_utils.py $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy swa_hybrid_reporting/reporting_utils.py"
    cp $IPROOT/coeus/swa_hybrid_reporting/connection_manager.py $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy swa_hybrid_reporting/connection_manager.py"
    cp $IPROOT/coeus/swa_hybrid_reporting/data_packager.py $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy swa_hybrid_reporting/data_packager.py"
    cp $IPROOT/coeus/swa_hybrid_reporting/package_observer.py $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy swa_hybrid_reporting/package_observer.py"
    #cp $IPROOT/coeus/swa_hybrid_reporting/ws_client.py $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    #|| fail 1 "Failed to copy swa_hybrid_reporting/ws_client.py"
    cp $IPROOT/scanners/picklelog_client.py $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy scanners/picklelog_client.py"

    #create a hard link for SWA hybrid reporting client to python2.7
    ln -f /usr/local/bin/python2.7 $PACKAGE_DIR/usr/local/bin/report_shipper_client

    #Copy websocket libraries
    cp -r /usr/local/lib/python2.7/site-packages/websocket $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy websocket module"
    cp -r /usr/local/lib/python2.7/site-packages/websocket_client-0.59.0.dist-info $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy websocket_client module"
    cp -r /usr/local/lib/python2.7/site-packages/yaml $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy yaml module"
    cp -r /usr/local/lib/python2.7/site-packages/watchdog $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy watchdog module"
    cp -r /usr/local/lib/python2.7/site-packages/pathtools $PACKAGE_DIR/data/swa_hybrid_reporting/ \
    || fail 1 "Failed to copy pathtools module"

    #Copy conf file, the ususal flow of installing the conf file is failing, thus, doing the copy operation here.
    cp $IPROOT/coeus/swa_hybrid_reporting/heimdall/report_shipper_client_release.conf $DATA_DESTDIR/etc/heimdall/report_shipper_client.conf \
    || fail 1 "Failed to copy report_shipper_client.conf file"

    echo "Ending `date` SWA hybrid reporting client installation"
}

copy_swgcert_key(){
mkdir -p $PACKAGE_DIR/data/db/swgcert
cp $IPROOT/coeus/prox/etc/swgcert/public.pem $PACKAGE_DIR/data/db/swgcert/
}

copy_libnikita_files() {
echo "******  Copying libnikita files ****** "
DISTROOT=$IPROOT/$IPPROD/release/distroot/usr/local/
cd $IPROOT/$IPPROD/packages/libnikita
(fetch http://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/libnikita-4.0.0.697.tar.gz ) || exit 1
( tar xf libnikita-4.0.0.697.tar.gz) || exit 1
(cp -r $IPROOT/$IPPROD/packages/libnikita/libnikita/usr/local/*  $PACKAGE_DIR/usr/local/ )
(cp -r $IPROOT/$IPPROD/packages/libnikita/libnikita/usr/local/* $DISTROOT ) || exit 1
echo "beaker done"
}

copy_beaker_files() {
echo " Copying Beaker files "
DISTROOT= $IPROOT/$IPPROD/release/distroot/usr/local/
cd $IPROOT/$IPPROD/packages/beaker
(fetch http://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/beaker-2.6.0.349.tar.gz) || exit 1
(tar xf beaker-2.6.0.349.tar.gz) || exit 1
(cp -r $IPROOT/$IPPROD/packages/beaker/beaker-2.6/usr/local/* $PACKAGE_DIR/usr/local/ )
(cp -r $IPROOT/$IPPROD/packages/beaker/beaker-2.6/usr/local/* $DISTROOT ) || exit 1
echo "beaker done"
}

copy_beaker_mod_nikita_files() {
DISTROOT=$IPROOT/$IPPROD/release/distroot/usr/local/
echo "****** Copy beaker-mod_nikita files ****** "
cd $IPROOT/$IPPROD/packages/beaker-mod_nikita
(fetch http://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/beaker-mod_nikita-2.2.0.649.tar.gz ) || exit 1
( tar xf beaker-mod_nikita-2.2.0.649.tar.gz) || exit 1
(cp -r $IPROOT/$IPPROD/packages/beaker-mod_nikita/mod/usr/local/* $PACKAGE_DIR/usr/local/ ) || exit 1
(cp -r $IPROOT/$IPPROD/packages/beaker-mod_nikita/mod/usr/local/* $DISTROOT ) || exit 1
echo "beaker-mod_nikita files done"
}
copy_libnikita-uri_files(){
echo "******  Copying libnikita-uri ****** "
DISTROOT=$IPROOT/$IPPROD/release/distroot/usr/local/
cd $IPROOT/$IPPROD/packages/libnikita
(fetch http://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/libnikita-uri-1.2.0.55.tar.gz ) || exit 1
( tar xf libnikita-uri-1.2.0.55.tar.gz) || exit 1
(cp -r $IPROOT/$IPPROD/packages/libnikita/libnikita-uri-1.2.0.55/usr/local/*  $PACKAGE_DIR/usr/local/ )
(cp -r $IPROOT/$IPPROD/packages/libnikita/libnikita-uri-1.2.0.55/usr/local/* $DISTROOT ) || exit 1
echo "beaker done"

}

copy_json-glib_files(){
echo "******  Copying json-glib ****** "
DISTROOT=$IPROOT/$IPPROD/release/distroot/usr/local/
cd $IPROOT/$IPPROD/packages/json-glib
(fetch  http://engci-maven.cisco.com/artifactory/content-security-builds-group/packages/json-glib-1.2.tar.gz ) || exit 1
(tar xf json-glib-1.2.tar.gz) || exit 1
(cp -r $IPROOT/$IPPROD/packages/json-glib/json-glib-1.2/usr/local/*  $PACKAGE_DIR/usr/local/ )
(cp -r $IPROOT/$IPPROD/packages/json-glib/json-glib-1.2/usr/local/*  $DISTROOT ) || exit 1
echo "json-glib done"

}


install_beaker_files(){
mkdir -p $PACKAGE_DIR/data/third_party/beaker
mkdir -p $PACKAGE_DIR/data/third_party/beaker/config
mkdir -p $PACKAGE_DIR/data/third_party/beaker/beakerdata
mkdir -p $PACKAGE_DIR/data/third_party/beaker/usr/local
mkdir -p $PACKAGE_DIR/data/db/beaker

cp $IPROOT/coeus/beaker/config/nikita.cfg $PACKAGE_DIR/data/third_party/beaker/config/
cp $IPROOT/coeus/beaker/beakerdb.tar.gz $PACKAGE_DIR/data/db/beaker/

copy_libnikita_files
copy_beaker_files
copy_beaker_mod_nikita_files
copy_libnikita-uri_files
echo "Building packages for beaker"
( cd $IPROOT/$IPPROD/packages/protobuf.beaker && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
( cd $IPROOT/$IPPROD/packages/protobuf.beaker/work/protobuf-3.5.1 && make && make install)
( cd $IPROOT/$IPPROD/packages/protobuf-c && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
( cd $IPROOT/$IPPROD/packages/tokyocabinet && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
( cd $IPROOT/$IPPROD/packages/lua && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
        #        ( cd $IPROOT/$IPPROD/packages/graphviz && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
copy_json-glib_files
#( cd $IPROOT/$IPPROD/packages/json-glib  && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR) || fail 1 "Failed to install json-glib"
         #       package_build  $IPROOT/$IPPROD/packages/vala && make install_beaker PACKAGE_DIR=$PACKAGE_DIR
( cd $IPROOT/$IPPROD/packages/intltool && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR) || fail 1 "Failed to install intltool"
( cd $IPROOT/$IPPROD/packages/libsoup && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)|| fail 1 "Failed to install libsoup"
         #       ( cd $IPROOT/$IPPROD/packages/libnikita && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
         #       ( cd $IPROOT/$IPPROD/packages/nettle && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
         #       ( cd $IPROOT/$IPPROD/packages/beaker && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
         #       ( cd $IPROOT/$IPPROD/packages/beaker-mod_nikita && make clean && make && make install && make install_beaker PACKAGE_DIR=$PACKAGE_DIR)
}

install_lasso() {
  srcdir=$IPROOT/third_party/lasso
  destdir=$DATA_DESTDIR
  echo " JWAL : ${srcdir} "
  echo " JWAL : ${DATA_DESTDIR}"
  build_lasso_depends || fail 1 "Building lasso dependenceis failed"
  echo " JWAL : build_lasso_depends done "
  # Since automake 1.16 is installed on FBSD13, adding required patch in autogen.sh
  patch -u -N $IPROOT/third_party/lasso/autogen.sh -i $IPROOT/third_party/patches/patch_lasso_autogen
  echo " JWAL : pathCH "
  #Fix for libintl issue while Installing Lasso.
  if [ ! -f libintl.so ]
  then
      cd /usr/local/lib && ln -s libintl.so.8.1.5 libintl.so
  fi
  echo "JWAL: libinitl"
  cd "$srcdir" && make clean
  cd "$srcdir" && rm -f m4/libtool.m4 m4/ltoptions.m4 m4/ltsugar.m4 m4/ltversion.m4 m4/lt~obsolete.m4
  echo "JWAL00 :rm"
#  cd "$srcdir" && ./autogen.sh --disable-dependency-tracking --disable-java --enable-python --disable-php4 --disable-php5 --disable-perl --exec-prefix=$destdir --prefix=$destdir  --with-python=$IPDATA/bin/python || fail 1 "Failed to build lasso"
   cd "$srcdir" && ./autogen.sh --disable-dependency-tracking --disable-java --enable-python --disable-php4 --disable-php5 --disable-perl --disable-gtk-doc --exec-prefix=$destdir --prefix=$destdir  --with-python=$IPDATA/bin/python || fail 1 "Failed to build lasso"
  echo "JWAL: gmake"
  PATH="$PATH:$IPDATA/bin" PYTHONPATH="" gmake -j4 install || fail 1 "Failed to install lasso"
}

install_datetimezone_utils() {
    echo "Building datetime utils for Python..."
    package_build $IPROOT/third_party/py-dateutil
    package_build /usr/ports/devel/py-pytz
}

install_imaging_lib() {
    echo "Building Imaging lib..."
    pkg_to_remove=`pkg info | grep jpeg | awk '{print $1}'`
    cd /usr/ports/graphics/jpeg-turbo
    rm -rf work
    make install
    cp -a /usr/ports/graphics/jpeg-turbo/work/stage/usr/local/lib/libjpeg.so* /usr/local/lib/
    cp /usr/local/lib/libjpeg.so* $DATA_DESTDIR/lib/
    cd $IPROOT/third_party/pil/
    $IPDATA/bin/python setup.py install
}

print_usage () {
    (
        cat <<EOF
This is IronPort's build script for Godspeed
usage: app_build.sh
  [ --as-tag=TAGNAME ]         Use TAGNAME for RCS Name: tags
  [ --log=PATH ]               Path of installation log
  [ --type=OS_ARCH ]           OS and Arch type
  [ --no-log ]                 Don't create installation log
  [ --only-python ]            Only build Python
  [ --no-python ]              Don't build Python
  [ --no-binaries]             Don't create binaries
  [ --no-testing-binaries]     Don't build Annihilator
  [ --only-testing-binaries]   Build the Annihilator tarball, not coeus
  [ --no-phoebe-binaries ]     Don't create messaging gateway binaries
  [ --no-package ]             Dont create FreeBSD packages
  [ --firestone ]              Build firestone
  [ --sandbox ]                Build sandbox
EOF
    )
}

# defaults
python=1
phoebe_binaries=1
testing_binaries=0
package=1
as_tag=""
firestone=0
sandbox_mode=0
type=""
# read optional command line arguments
while [ "x$1" != "x" ]
do
    case "$1" in
    --as-tag=*)
        as_tag=`echo "$1" | sed -e 's/[^=]*=//'`
        ;;
    --as-tag|-astag)
        shift
        as_tag="$1"
        ;;
    --type=*)
        type=`echo "$1" | sed -e 's/[^=]*=//'`
        ;;
    --type|-type)
        shift
        type="$1"
        ;;
    --log=*|-log=*)
        logpath=`echo "$1" | sed -e 's/[^=]*=//'`
        ;;
    --log|-log)
        shift
        logpath="$1"
        ;;
    --no-log|-nolog)
        logpath="/dev/null"
        ;;
    --only=python|--only-python|-onlypython|-onlyinstallpython)
        python=1
        testing_binaries=0
        phoebe_binaries=0
        ;;
    --no-python|-nopython)
        python=0
        ;;
    --no-binaries|-nobinaries)
        phoebe_binaries=0
        testing_binaries=0
        package=0
        ;;
    --no-testing-binaries|-notestingbinaries)
        testing_binaries=0
        ;;
    --no-phoebe-binaries|-nophoebebinaries)
        phoebe_binaries=0
        ;;
    --only-testing-binaries|-onlytestingbinaries)
        phoebe_binaries=0
        testing_binaries=1
        ;;
    --no-package|-nopackage)
        package=0
        ;;
    --firestone)
        python=1
        phoebe_binaries=0
        testing_binaries=0
        package=0
        firestone=1
        ;;
    --sandbox)
        python=1
        phoebe_binaries=1
        sandbox_mode=1
        testing_binaries=0
        package=1
        firestone=0
        ;;
    --help|--usage|-h|-help|-usage|-\?)
        print_usage
        fail 0
        ;;
    *)
        print_usage
        echo "Unknown argument: $1"
        fail
        ;;
    esac
    shift
done

starttime=`date`

echo ""
echo "Starting $0..."

if [ "x$sandbox_mode" != "x1" ]
then
   freebsd_8_amd64_gmake_check
fi # !sandbox

# Clear out the package directory so we can start fresh
rm -rf $PACKAGE_DIR

if [ "$as_tag" = "" ]
then
    as_tag="exp-$USER-9-9-9-999"
    echo "--as-tag not specified, using $as_tag"
fi

if [ "x$sandbox_mode" = "x1" ]
then
    as_tag="sandbox-$as_tag"
fi

PACKAGE_NAME=$as_tag
export DATA_DESTDIR=$PACKAGE_DIR/data/release/$as_tag

version_parse_tag() {
    local tag n n3dashed n4dashed
    tag="$1"
    build="$tag"
    n='[0-9][0-9]*'
    n3dashed="$n-$n-$n"
    n4dashed="$n3dashed-$n"
    # add build=000, subminor_number=0,
    # or product-major-minor-subminor=exp-0-0-0 as needed
    echo "$tag" \
        | sed -ne '/-'$n4dashed'/!{s/\(-'$n'-'$n'\)-\('$n'\)/\1-0-\2/;}' \
              -e '/-'$n4dashed'/!{s/\(-'$n'-'$n'\)/\1-000/;}' \
              -e '/-'$n3dashed'/!{s/^/exp-0-0-0-/;}' \
              -e 's/-\('$n'\)-\('$n'\)-\('$n'\)-\(.*\)/ MAJOR_NUMBER=\1 MINOR_NUMBER=\2 SUBMINOR_NUMBER=\3 BUILD="\4"/' \
              -e 's/\([^ ]*\) \(.*\)/PRODUCT="\1" \2/p'
}

eval $(version_parse_tag "$as_tag")

# Install Python

if [ "x$python" = "x1" ]
then
    install_python
fi

PYTHONPATH=`$IPDATA/bin/python $IPROOT/coeus/python_path.py $IPROOT`
export PYTHONPATH

PYTHON_VER=`$IPDATA/bin/python -c "import distutils.sysconfig;print distutils.sysconfig.get_python_version()"`
PYTHON_LIB_DIR="$IPDATA/lib/python${PYTHON_VER}"
PYTHON_DESTDIR="$DATA_DESTDIR/lib/python${PYTHON_VER}/site-packages"

if [ "x$sandbox_mode" != "x1" ]
then
    #Build Swig and Python
    echo "Build Swig and Unbound: Python${PYTHON_VER}"
    destdir=`pwd`/distroot/usr/local
    mkdir -p $destdir/bin/
    mkdir -p $destdir/share/swig/
    (cd  $IPROOT/third_party/swig && ./configure --disable-ccache --without-pcre --with-python=/data/lib/python${PYTHON_VER}/site-packages && ( \
         make && make install )) || fail 1 "packages/file compilation failed"

    echo "Installing unbound library"
    export PYTHON_LDFLAGS="-L/usr/local/lib -L/data/lib/python${PYTHON_VER} /data/lib/libpython${PYTHON_VER}.a -lm -lz -lutil -lcrypto"
    (cd  $IPROOT/third_party/unbound && ./configure --with-pyunbound --prefix=$destdir && ( \
         make && make install )) || fail 1 "packages/file compilation failed"

    cp -a $IPROOT/third_party/unbound/.libs/*.so* /lib/
    cp -a $IPROOT/third_party/unbound/.libs/*.so* $PYTHON_LIB_DIR
    cp -a $IPROOT/third_party/unbound/libunbound/python/unbound.py $PYTHON_LIB_DIR
    cp -a $IPROOT/third_party/unbound/.libs/_unbound.so $PYTHON_LIB_DIR
fi

# TODO : This is a temporary fix, Need to remove it in future.
if [ "x$type" = "xfreebsd_10_amd64_build" ]
then
    cp -a $IPROOT/third_party/unbound/.libs/*.so* /lib/
    cp -a $IPROOT/third_party/unbound/.libs/*.so* $PYTHON_LIB_DIR
    cp -a $IPROOT/third_party/unbound/libunbound/python/unbound.py $PYTHON_LIB_DIR
    cp -a $IPROOT/third_party/unbound/.libs/_unbound.so $PYTHON_LIB_DIR
fi

# Build Webtapd
(cd $IPROOT/scanners/webtapd && ./setup_webtapd $PACKAGE_DIR/data ) || fail 1 "Cannot setup webtapd"

# Build reporting.
(cd $IPROOT/ap/reporting || fail 1 "Failed to cd to reporting."
 ./setup_reporting || fail 1 "Failed to set up the reporting system."
) || fail 1 "Failed to set up the reporting system."

if [ "x$sandbox_mode" != "x1" ]
then
  # Build haystack.
  (cd $IPROOT/ap/reporting/haystack || fail 1 "Failed to cd to haystack."
   ./setup_haystack || fail 1 "Failed to set up the haystack reporting system."
  ) || fail 1 "Failed to set up the haystack reporting system."
fi # sandbox

# Build iccm.
(cd $IPROOT/ap/iccm || fail 1 "Failed to cd to iccm."
 ./setup_iccm || fail 1 "Failed to set up the iccm system."
) || fail 1 "Failed to set up the iccm system."

# Build SMAD.
(cd $IPROOT/ap/smad || fail 1 "Failed to cd to smad."
 ./setup_smad || fail 1 "Failed to set up the smad system."
) || fail 1 "Failed to set up the smad system."

# Build Updater.
(cd $IPROOT/ap/updater_client || fail 1 "Failed to cd to updater_client."
 ./setup_updater || fail 1 "Failed to set up the updater client."
) || fail 1 "Failed to set up the updater client."

# Build snmp
(cd $IPROOT/ap/snmp || fail 1 "Failed to cd to snmp."
 ./setup_snmp || fail 1 "Failed to setup snmp."
) || fail 1 "Failed to setup snmp."

# Build ntp
(cd $IPROOT/ap/ntp || fail 1 "Failed to cd to ntp."
 ./setup_ntp || fail 1 "Failed to setup ntp."
) || fail 1 "Failed to setup ntp."

# Build sandbox
(cd $IPROOT/ap/sandbox || fail 1 "Failed to cd to sandbox."
 ./setup_sandbox || fail 1 "Failed to setup sandbox."
) || fail 1 "Failed to setup sandbox."

# Build qlog
(cd $IPROOT/ap/qlog || fail 1 "Failed to cd to qlog."
 ./setup_qlog || fail 1 "Failed to setup qlog."
) || fail 1 "Failed to setup qlog."

# Build ftpd
(cd $IPROOT/ap/ftpd || fail 1 "Failed to cd to ftpd."
 ./setup_ftpd || fail 1 "Failed to setup ftpd."
) || fail 1 "Failed to setup ftpd."

# Build ocspd
(cd $IPROOT/ap/ocsp || fail 1 "Failed to cd to ocsp."
 ./setup_ocsp || fail 1 "Failed to setup ocsp."
) || fail 1 "Failed to setup ocsp."

# Build feedsd
(cd $IPROOT/ap/feedsd || fail 1 "Failed to cd to feedsd."
 ./setup_feedsd || fail 1 "Failed to setup feedsd."
) || fail 1 "Failed to setup feedsd."

# Build pyrad
(cd $IPROOT/third_party/pyrad || fail 1 "Failed to cd to pyrad."
 ./setup_pyrad || fail 1 "Failed to setup pyrad."
) || fail 1 "Failed to setup pyrad."

# Build features
(cd $IPROOT/ap/features || fail 1 "Failed to cd to features."
 ./setup_features || fail 1 "Failed to setup features."
) || fail 1 "Failed to setup features."

# Build vmtoolsd
(cd $IPROOT/ap/vmtoolsd || fail 1 "Failed to cd to vmtoolsd."
 ./setup_vmtoolsd || fail 1 "Failed to setup vmtoolsd."
) || fail 1 "Failed to setup vmtoolsd."

create_directories

if [ "x$firestone" = "x1" ]
then
    build_firestone
    exit 0
fi

# Create binaries
if [ "x$phoebe_binaries" = "x1" ]
then
    create_supplemental_binaries
fi

if [ "x$sandbox_mode" != "x1" ]
then
    if [ -d "$IPROOT/coeus/release/codeCoverage" ]
    then
    (
        echo '***in app_build.sh changing compiler from clang3.4.1 to clang3.9 for code coverage***'
        code_coverage_feature enable
        echo '*** openssl is compile using clang3.9 for prox code coverage ***'
        (cd $IPROOT/ap/ciscossl && make clean install ) || exit 1
    ) || fail 1 "app_build.sh Failed to replace clang3.9 compailer"
    fi #coverage feature end
    #create_merlin_binary
    #install_webcat
    create_coeus_debug_tools
    if [ "$PERF_TOOLS" = "1" ]
    then
        install_coeus_perf_tools
    fi
    download_prebuilt_packages
    install_redis_module
    create_https_utils_binaries
    create_ised_binaries
    package_build_nats_server
    package_build_protobuf
    package_build_protobuf_c
    package_build_nats_client
    package_build_cxxopts
    package_build_yaml_cpp
    package_build_bitdefender
    create_prox_binaries
    install_onbox_dlp
    install_adaptive_scanning
    install_archive_scanner
    install_icap_test
    install_webtapd
    if [ -d "$IPROOT/coeus/release/codeCoverage" ]
    then
    (
        echo '***in app_build.sh default clang3.4.1 compiler***'
        code_coverage_feature disable
    ) || fail 1 "app_build.sh Failed to replace clang3.4.1 compailer"
    fi # coverage feature end
fi # end of sandbox mode check

# Copy the dummy Service Provider certificate.
cp $IPROOT/coeus/samld/samld/dummy_sp_cert.crt $PACKAGE_DIR/data/db/saml20

# Copy the RADIUS attributes dictionary files
cp $IPROOT/coeus/uds/uds/dictionary* $PACKAGE_DIR/data/db/radius

# Copy the SSE server list to sse_connector_data directory
cp $IPROOT/coeus/sse_connector/heimdall/fqdn_server_list.txt $PACKAGE_DIR/data/db/sse_connector_data/fqdn_server_list.txt
chmod 777 $PACKAGE_DIR/data/db/sse_connector_data/fqdn_server_list.txt

# Copy the SSE config file to sse_connector_data directory
cp $IPROOT/coeus/sse_connector/heimdall/config.toml $PACKAGE_DIR/data/db/sse_connector_data/config.toml
chmod 644 $PACKAGE_DIR/data/db/sse_connector_data/config.toml

echo "############################### "
echo "# Install SSE Connector binary  "
echo "############################### "

echo "Starting `date` install SSE connector"
dirname=sse_temp
mkdir -p -- "$IPDATA/$dirname"
tempdir=$IPDATA/$dirname
destdir=$PACKAGE_DIR/data/third_party/connector
sse_connector_src_file=connector_freebsd_amd64_2.0.11.tgz
sse_connector_target_file=connector
sse_connector_server_path=https://engci-maven-master.cisco.com/artifactory/sbg-cloudinfra-connector-rel/2.0.11/
(cd $tempdir && fetch --no-verify-peer $sse_connector_server_path/$sse_connector_src_file && tar -xvf $sse_connector_src_file && cp $sse_connector_target_file/$sse_connector_target_file $destdir/ && chmod 755 $destdir/$sse_connector_target_file && cd .. && rm -rf $tempdir) || fail 1 "Failed to install SSE connector binary"
echo "Ending `date` install SSE connector"

if [ "x$phoebe_binaries" = "x1" ] || [ "x$testing_binaries" = "x1" ]
then
    create_frozen_binary
    create_stat_prof # This doesn't do anything
fi

BOOTSTRAP=$IPROOT/ap/ipoe/build/bootstrap
WRAPPER=$IPROOT/freebsd/bootstrap/generic_wrapper.sh
NO_CD_WRAPPER=$IPROOT/freebsd/bootstrap/no_cd_wrapper.sh

# Copy everything to the package directory

if [ "x$phoebe_binaries" = "x1" -a "x$sandbox_mode" != "x1" ]
then
    install_binaries
    install_magic_db
    (cd $IPROOT/scanners/fire_amp && ./setup_amp $PACKAGE_DIR/data ) || fail 1 "Cannot setup amp"
    #(cd $IPROOT/coeus/ised && ./setup_ise $PACKAGE_DIR/data ) || fail 1 "Cannot setup ISE"
    (cd $IPROOT/coeus/timezone_checker && ./setup_checker $PACKAGE_DIR/data ) || fail 1 "Cannot setup timezone_checker"
    copy_config
    install_startup_scripts
    install_csborg_script
    install_enablediag
    install_adminpassword
    install_samba_conf_files
    install_wbrs
    install_firestone
    install_avc_engine
    install_updater
    install_default_tm_blacklist
    install_trusted_ca_file
    install_unbound_root_key
    install_updater_bundle_file
    install_internal_ca_file
    install_openssl_cnf_file
    install_comodo_crl_file
    #copy_kdump_dependent_libs
    copy_certificates
    install_key_generator
    install_global_configuration
    install_version_file
    install_counters
    install_counterd_conf
    install_install_modes
    install_updater_manifest
    install_support_request_data
    install_default_password_word_files
    install_lasso
    install_clamav
    create_beaker_monitor
    install_beaker_updater
    install_beaker_files
    install_ytc_files
    copy_swgcert_key
    #install_datetimezone_utils
    install_jre
    install_jre_smart_agent
    install_smart_license_packages
    install_haystack
    install_net_snmp
    install_logcollector
    install_external_auth
    install_imaging_lib
    install_nginx
    install_eun_pages
    install_coverage_script
    create_symlinks
    install_cs-borg-dc
    install_adc_engine
    install_umbrella_client
    install_report_shipper_client
fi

# Bivash Added as snmp header file required#
if [ "x$sandbox_mode" != "x1" ]
then
    install_prox_mib_agent
    temp_third_party_utils_copy
fi #end of non sandbox mode
# Bivash Added as snmp header file required#

if [ "x$sandbox_mode" = "x1" ]
then
    install_binaries
    (cd $IPROOT/coeus/ised && ./setup_ise $PACKAGE_DIR/data sandbox ) || fail 1 "Cannot setup ISE"
    copy_config
    install_internal_ca_file
    install_trusted_ca_file
    install_openssl_cnf_file
    install_comodo_crl_file
    copy_certificates
    install_version_file
    install_lasso
    copy_libs
    create_symlinks
    mv $PACKAGE_DIR/data/release/$as_tag $PACKAGE_DIR/data/release/current
fi

if [ "x$testing_binaries" = "x1" ]
then
    install_testing_binaries
fi

if [ "x$package" = "x1" ]
then
    make_packages
fi

echo "--------------------------------"
echo ""
echo "App Build started:  $starttime"
echo "App Build finished: "`date`
echo 'App Build revision: $Revision$'
echo "App Build log:      $logpath"