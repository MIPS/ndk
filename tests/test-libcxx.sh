#!/bin/bash

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -z "$NDK" ]; then
    >&2 echo "Error: $$NDK must be set in your environment."
    exit 1
fi

function usage() {
    >&2 echo "usage: $(basename $0) ABI API_LEVEL"
}

ABI=$1
if [ -z "$ABI" ]; then
    usage
    exit 1
fi

API=$2
if [ -z "$API" ]; then
    usage
    exit 1
fi

case "$ABI" in
    armeabi*)
        ARCH=arm
        TRIPLE=arm-linux-androideabi
        TOOLCHAIN=$TRIPLE
        ;;
    arm64-v8a)
        ARCH=arm64
        TRIPLE=aarch64-linux-android
        TOOLCHAIN=$TRIPLE
        ;;
    mips)
        ARCH=mips
        TRIPLE=mipsel-linux-android
        TOOLCHAIN=$TRIPLE
        ;;
    mips64)
        ARCH=mips64
        TRIPLE=mips64el-linux-android
        TOOLCHAIN=$TRIPLE
        ;;
    x86)
        ARCH=x86
        TRIPLE=i686-linux-android
        TOOLCHAIN=x86
        ;;
    x86_64)
        ARCH=x86_64
        TRIPLE=x86_64-linux-android
        TOOLCHAIN=x86_64
        ;;
    *)
        >&2 echo "Unknown ABI: $ABI"
        exit 1
        ;;
esac

HOST_TAG=linux-x86_64

LIT=$THIS_DIR/../../external/llvm/utils/lit/lit.py
LIT_ARGS=${@:2}

LIBCXX_DIR=$NDK/sources/cxx-stl/llvm-libc++/libcxx
sed -e "s:%ABI%:$ABI:g" -e "s:%TRIPLE%:$TRIPLE:g" \
    -e "s:%ARCH%:$ARCH:g" -e "s:%TOOLCHAIN%:$TOOLCHAIN:g" \
    -e "s:%API%:$API:g" \
    $LIBCXX_DIR/test/lit.ndk.cfg.in > $LIBCXX_DIR/test/lit.site.cfg

adb push $LIBCXX_DIR/../libs/$ABI/libc++_shared.so /data/local/tmp
$LIT -sv $LIT_ARGS $LIBCXX_DIR/test
