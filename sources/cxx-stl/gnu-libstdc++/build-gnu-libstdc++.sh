#!/bin/sh
#
# Copyright (C) 2011 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#  This shell script is used to rebuild the prebuilt GNU libsupc++ and
#  libstdc++ binaries from their sources. It requires an NDK installation
#  that contains valid plaforms files and toolchain binaries.
#

# include common function and variable definitions
. $NDK_BUILDTOOLS_PATH/prebuilt-common.sh

STL_DIR=sources/cxx-stl
GNUSTL_DIR=gnu-libstdc++

PROGRAM_PARAMETERS="<src-dir>"

PROGRAM_DESCRIPTION=\
"Rebuild the prebuilt GNU libsupc++ / libstdc++ binaries for the Android NDK.

This script is called when packaging a new NDK release. It will simply
rebuild the GNU libsupc++ and libstdc++ static and shared libraries from
sources.

This requires a temporary NDK installation containing platforms and
toolchain binaries for all target architectures, as well as the path to
the corresponding gcc source tree.

By default, this will try with the current NDK directory, unless
you use the --ndk-dir=<path> option.

The output will be placed in appropriate sub-directories of
<ndk>/$GNUSTL_SUBDIR, but you can override this with the --out-dir=<path>
option.
"

GCC_VERSION_LIST=
register_var_option "--gcc-version-list=<vers>" GCC_VERSION_LIST "List of GCC versions"

PACKAGE_DIR=
register_var_option "--package-dir=<path>" PACKAGE_DIR "Put prebuilt tarballs into <path>."

NDK_DIR=
register_var_option "--ndk-dir=<path>" NDK_DIR "Specify NDK root path for the build."

BUILD_DIR=
register_var_option "--build-dir=<path>" BUILD_DIR "Specify temporary build dir."

OUT_DIR=
register_var_option "--out-dir=<path>" OUT_DIR "Specify output directory directly."

ABIS=$(spaces_to_commas $PREBUILT_ABIS)
register_var_option "--abis=<list>" ABIS "Specify list of target ABIs."

NO_MAKEFILE=
register_var_option "--no-makefile" NO_MAKEFILE "Do not use makefile to speed-up build"

VISIBLE_LIBGNUSTL_STATIC=
register_var_option "--visible-libgnustl-static" VISIBLE_LIBGNUSTL_STATIC "Do not use hidden visibility for libgnustl_static.a"

WITH_DEBUG_INFO=
register_var_option "--with-debug-info" WITH_DEBUG_INFO "Build with -g.  STL is still built with optimization but with debug info"

WITH_LIBSUPPORT=
register_var_option "--with-libsupport" WITH_LIBSUPPORT "Build with -landroid_support."

register_jobs_option
register_try64_option

extract_parameters "$@"

# set compiler version to any even earlier than default
EXPLICIT_COMPILER_VERSION=1
if [ -z "$GCC_VERSION_LIST" ]; then
    EXPLICIT_COMPILER_VERSION=
    GCC_VERSION_LIST=$DEFAULT_GCC_VERSION_LIST
fi

SRCDIR=$(echo $PARAMETERS | sed 1q)
check_toolchain_src_dir "$SRCDIR"

ABIS=$(commas_to_spaces $ABIS)

# Handle NDK_DIR
if [ -z "$NDK_DIR" ] ; then
    NDK_DIR=$ANDROID_NDK_ROOT
    log "Auto-config: --ndk-dir=$NDK_DIR"
else
    if [ ! -d "$NDK_DIR" ] ; then
        echo "ERROR: NDK directory does not exists: $NDK_DIR"
        exit 1
    fi
fi

HOST_TAG_LIST="$HOST_TAG $HOST_TAG32"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
fail_panic "Could not create build directory: $BUILD_DIR"

# $1: ABI name
# $2: Build directory
# $3: "static" or "shared"
# $4: GCC version
# $5: optional "thumb"
build_gnustl_for_abi ()
{
    local ARCH BINPREFIX SYSROOT GNUSTL_SRCDIR
    local ABI=$1
    local BUILDDIR="$2"
    local LIBTYPE="$3"
    local GCC_VERSION="$4"
    local DSTDIR=$NDK_DIR/$GNUSTL_SUBDIR/libs/$ABI
    local PREBUILT_NDK=$ANDROID_BUILD_TOP/prebuilts/ndk/current
    local SRC OBJ OBJECTS CFLAGS CXXFLAGS CPPFLAGS

    prepare_target_build $ABI $PLATFORM $NDK_DIR
    fail_panic "Could not setup target build."

    INSTALLDIR=$BUILDDIR/install-$ABI-$GCC_VERSION
    BUILDDIR=$BUILDDIR/$LIBTYPE-${ABI}j$GCC_VERSION

    mkdir -p $DSTDIR

    ARCH=$(convert_abi_to_arch $ABI)
    for TAG in $HOST_TAG_LIST; do
        BINPREFIX=$ANDROID_BUILD_TOP/prebuilts/ndk/current/$(get_toolchain_binprefix_for_arch $ARCH $GCC_VERSION $TAG)
        if [ -f ${BINPREFIX}gcc ]; then
            break;
        fi
    done
    GNUSTL_SRCDIR=$SRCDIR/gcc/gcc-$GCC_VERSION/libstdc++-v3
    # Sanity check
    if [ ! -d "$GNUSTL_SRCDIR" ]; then
        echo "ERROR: Not a valid toolchain source tree."
        echo "Can't find: $GNUSTL_SRCDIR"
        exit 1
    fi

    if [ ! -f "$GNUSTL_SRCDIR/configure" ]; then
        echo "ERROR: Configure script missing: $GNUSTL_SRCDIR/configure"
        exit 1
    fi

    SYSROOT=$PREBUILT_NDK/$(get_default_platform_sysroot_for_arch $ARCH)
    LDIR=$SYSROOT"/usr/"$(get_default_libdir_for_arch $ARCH)
    # Sanity check
    if [ ! -f "$LDIR/libc.a" ]; then
      echo "ERROR: Incomplete sysroot, $LDIR/libc.a not found"
      exit 1
    fi
    if [ ! -f "$LDIR/libc.so" ]; then
        echo "ERROR: Incomplete sysroot. $LDIR/libc.so not found"
        exit 1
    fi

    EXTRA_CFLAGS="-ffunction-sections -fdata-sections"
    EXTRA_LDFLAGS="-Wl,--build-id"

    # arm32 libs are built as thumb.
    if [ "$ABI" != "${ABI%%arm*}" -a "$ABI" = "${ABI%%64*}" ] ; then
        EXTRA_CFLAGS="$EXTRA_CFLAGS -mthumb"
        EXTRA_LDFLAGS="$EXTRA_LDFLAGS -mthumb"
    fi

    case $ARCH in
        arm)
            BUILD_HOST=arm-linux-androideabi
            ;;
        arm64)
            BUILD_HOST=aarch64-linux-android
            ;;
        x86)
            BUILD_HOST=i686-linux-android
            # ToDo: remove the following once all x86-based device call JNI function with
            #       stack aligned to 16-byte
            EXTRA_CFLAGS="$EXTRA_CFLAGS -mstackrealign"
            ;;
        x86_64)
            BUILD_HOST=x86_64-linux-android
            # ToDo: remove the following once all x86-based device call JNI function with
            #       stack aligned to 16-byte
            EXTRA_CFLAGS="$EXTRA_CFLAGS -mstackrealign"
            ;;
        mips)
            BUILD_HOST=mipsel-linux-android
            ;;
        mips64)
            BUILD_HOST=mips64el-linux-android
            ;;
    esac

    # Copy the sysroot to a temporary build directory
    run mkdir -p "$BUILDDIR/sysroot"
    run cp -RHL "$SYSROOT"/* "$BUILDDIR/sysroot"
    SYSROOT=$BUILDDIR/sysroot
    BUILDDIR=$BUILDDIR/build
    # Ensure multilib toolchains can use sysroot
    if [ ! -d "$SYSROOT/usr/lib64" ] ; then
        mkdir "$SYSROOT/usr/lib64"
    fi

    CFLAGS="-fPIC $CFLAGS --sysroot=$SYSROOT -fexceptions -funwind-tables -D__BIONIC__ -O2 $EXTRA_CFLAGS"
    CXXFLAGS="-fPIC $CXXFLAGS --sysroot=$SYSROOT -fexceptions -frtti -funwind-tables -D__BIONIC__ -O2 $EXTRA_CFLAGS"
    CPPFLAGS="$CPPFLAGS --sysroot=$SYSROOT"
    if [ "$WITH_DEBUG_INFO" ]; then
        CFLAGS="$CFLAGS -g"
        CXXFLAGS="$CXXFLAGS -g"
    fi
    if [ "$WITH_LIBSUPPORT" ]; then
        CFLAGS="$CFLAGS -I$NDK_DIR/$SUPPORT_SUBDIR/include"
        CXXFLAGS="$CXXFLAGS -I$NDK_DIR/$SUPPORT_SUBDIR/include"
        EXTRA_LDFLAGS="$EXTRA_LDFLAGS -L$NDK_DIR/$SUPPORT_SUBDIR/libs/$ABI -landroid_support"
    fi
    export CFLAGS CXXFLAGS CPPFLAGS

    export CC=${BINPREFIX}gcc
    export CXX=${BINPREFIX}g++
    export AS=${BINPREFIX}as
    export LD=${BINPREFIX}ld
    export AR=${BINPREFIX}ar
    export RANLIB=${BINPREFIX}ranlib
    export STRIP=${BINPREFIX}strip

    setup_ccache

    export LDFLAGS="$EXTRA_LDFLAGS -lc"

    case $ABI in
        armeabi-v7a)
            CXXFLAGS=$CXXFLAGS" -march=armv7-a -mfpu=vfpv3-d16 -mfloat-abi=softfp"
            LDFLAGS=$LDFLAGS" -Wl,--fix-cortex-a8"
            ;;
        arm64-v8a)
            CFLAGS="$CFLAGS -mfix-cortex-a53-835769"
            CXXFLAGS=$CXXFLAGS" -mfix-cortex-a53-835769"
            ;;
        mips)
            # $CFLAGS are not used for all configure steps,
            # ensure -mips32 flag is provided using $CC.
            CC="$CC -mips32"
            CXX="$CXX -mips32"
            AS="$AS -mips32"
            LDFLAGS="$LDFLAGS -mips32"
            ;;
        mips32r6)
            CC="$CC -mips32r6 -mno-odd-spreg"
            CXX="$CXX -mips32r6 -mno-odd-spreg"
            AS="$AS -mips32r6 -mno-odd-spreg"
            CFLAGS="$CFLAGS -mips32r6 -mno-odd-spreg -B$BINPREFIX"
            CXXFLAGS="$CXXFLAGS -mips32r6 -mno-odd-spreg -B$BINPREFIX"
            LDFLAGS="$LDFLAGS -mips32r6 -mno-odd-spreg -B$BINPREFIX"
            ;;
    esac

    if [ "$ABI" = "armeabi" -o "$ABI" = "armeabi-v7a" ]; then
        CFLAGS=$CFLAGS" -minline-thumb1-jumptable"
        CXXFLAGS=$CXXFLAGS" -minline-thumb1-jumptable"
    fi

    LIBTYPE_FLAGS=
    if [ $LIBTYPE = "static" ]; then
        # Ensure we disable visibility for the static library to reduce the
        # size of the code that will be linked against it.
        if [ -z "$VISIBLE_LIBGNUSTL_STATIC" ] ; then
            LIBTYPE_FLAGS="--enable-static --disable-shared"
            LIBTYPE_FLAGS=$LIBTYPE_FLAGS" --disable-libstdcxx-visibility"
            CXXFLAGS=$CXXFLAGS" -fvisibility=hidden -fvisibility-inlines-hidden"
        fi
    else
        LIBTYPE_FLAGS="--disable-static --enable-shared"
        #LDFLAGS=$LDFLAGS" -lsupc++"
    fi

    MULTILIB_FLAGS=--disable-multilib

    INCLUDE_VERSION=`cat $GNUSTL_SRCDIR/../gcc/BASE-VER`
    PROJECT="gnustl_$LIBTYPE gcc-$GCC_VERSION $ABI"
    echo "$PROJECT: configuring"
    mkdir -p $BUILDDIR && rm -rf $BUILDDIR/* &&
    cd $BUILDDIR &&
    run $GNUSTL_SRCDIR/configure \
        --enable-bionic-libs \
        --prefix=$INSTALLDIR \
        --host=$BUILD_HOST \
        $LIBTYPE_FLAGS \
        --enable-libstdcxx-time \
        --disable-symvers \
        $MULTILIB_FLAGS \
        --disable-nls \
        --disable-sjlj-exceptions \
        --disable-tls \
        --disable-libstdcxx-pch \
        --with-gxx-include-dir=$INSTALLDIR/include/c++/$INCLUDE_VERSION

    fail_panic "Could not configure $PROJECT"

    echo "$PROJECT: compiling"
    run make -j$NUM_JOBS
    fail_panic "Could not build $PROJECT"

    echo "$PROJECT: installing"
    run make install
    fail_panic "Could not create $ABI prebuilts for GNU libsupc++/libstdc++"
}


HAS_COMMON_HEADERS=

# $1: ABI
# $2: Build directory
# $3: GCC_VERSION
copy_gnustl_libs ()
{
    local ABI="$1"
    local BUILDDIR="$2"
    local ARCH=$(convert_abi_to_arch $ABI)
    local GCC_VERSION="$3"

    local GNUSTL_SRCDIR=$SRCDIR/gcc/gcc-$GCC_VERSION/libstdc++-v3
    local INCLUDE_VERSION=`cat $GNUSTL_SRCDIR/../gcc/BASE-VER`

    local SDIR="$BUILDDIR/install-$ABI-$GCC_VERSION"
    local DDIR="$NDK_DIR/$GNUSTL_SUBDIR"

    local GCC_VERSION_NO_DOT=$(echo $GCC_VERSION|sed 's/\./_/g')
    # Copy the common headers only once per gcc version
    if [ -z `var_value HAS_COMMON_HEADERS_$GCC_VERSION_NO_DOT` ]; then
        copy_directory "$SDIR/include/c++/$INCLUDE_VERSION" "$DDIR/include"
        rm -rf "$DDIR/include/$BUILD_HOST"
	eval HAS_COMMON_HEADERS_$GCC_VERSION_NO_DOT=true
    fi

    rm -rf "$DDIR/libs/$ABI" &&
    mkdir -p "$DDIR/libs/$ABI/include"

    # Copy the ABI-specific headers
    copy_directory "$SDIR/include/c++/$INCLUDE_VERSION/$BUILD_HOST/bits" "$DDIR/libs/$ABI/include/bits"

    local LDIR=lib
    if [ "$ARCH" != "${ARCH%%64*}" ]; then
        #Can't call $(get_default_libdir_for_arch $ARCH) which contain hack for arm64
        LDIR=lib64
    fi

    if [ "$ABI" = "mips32r6" ]; then
        LDIR=libr6
    fi

    # Copy the ABI-specific libraries
    # Note: the shared library name is libgnustl_shared.so due our custom toolchain patch
    copy_file_list "$SDIR/$LDIR" "$DDIR/libs/$ABI" libsupc++.a libgnustl_shared.so

    # Note: we need to rename libgnustl_shared.a to libgnustl_static.a
    cp "$SDIR/$LDIR/libgnustl_shared.a" "$DDIR/libs/$ABI/libgnustl_static.a"

    if [ -d "$SDIR/thumb" ] ; then
        copy_file_list "$SDIR/thumb/$LDIR" "$DDIR/libs/$ABI/thumb" libsupc++.a libgnustl_shared.so
        cp "$SDIR/thumb/$LDIR/libgnustl_shared.a" "$DDIR/libs/$ABI/thumb/libgnustl_static.a"
    fi
}

GCC_VERSION_LIST=$(commas_to_spaces $GCC_VERSION_LIST)
for ABI in $ABIS; do
    ARCH=$(convert_abi_to_arch $ABI)
    FIRST_GCC_VERSION=$(get_first_gcc_version_for_arch $ARCH)
    for VERSION in $GCC_VERSION_LIST; do
        # Only build for this GCC version if it on or after FIRST_GCC_VERSION
        if [ -z "$EXPLICIT_COMPILER_VERSION" ] && ! version_is_at_least "${VERSION%%l}" "$FIRST_GCC_VERSION"; then
            continue
        fi

        build_gnustl_for_abi $ABI "$BUILD_DIR" static $VERSION
        build_gnustl_for_abi $ABI "$BUILD_DIR" shared $VERSION

        copy_gnustl_libs $ABI "$BUILD_DIR" $VERSION
    done
done

# If needed, package files into tarballs
if [ -n "$PACKAGE_DIR" ] ; then
    FILES="$GNUSTL_DIR/Android.mk $GNUSTL_DIR/include"
    for ABI in $ABIS; do
        if [ ! -d "$NDK_DIR/$GNUSTL_SUBDIR/libs/$ABI" ]; then
            continue
        fi
        case "$ABI" in
            x86_64)
                MULTILIB="include/32/bits include/x32/bits
                          lib/libsupc++.a lib/libgnustl_static.a lib/libgnustl_shared.so
                          libx32/libsupc++.a libx32/libgnustl_static.a libx32/libgnustl_shared.so
                          lib64/libsupc++.a lib64/libgnustl_static.a lib64/libgnustl_shared.so"
                ;;
            mips64)
                MULTILIB="lib64/libsupc++.a lib64/libgnustl_static.a lib64/libgnustl_shared.so"
                ;;
            mips|mips32r6)
                MULTILIB="include/mips-r6/bits
                          lib/libsupc++.a lib/libgnustl_static.a lib/libgnustl_shared.so
                          libr6/libsupc++.a libr6/libgnustl_static.a libr6/libgnustl_shared.so"
                ;;
            *)
                MULTILIB=
                ;;
        esac
        for LIB in include/bits $MULTILIB libsupc++.a libgnustl_static.a libgnustl_shared.so; do
            FILES="$FILES $GNUSTL_DIR/libs/$ABI/$LIB"
        done
    done

    make_repo_prop "$NDK_DIR/$STL_DIR/$GNUSTL_DIR"
    FILES="$FILES $GNUSTL_DIR/repo.prop"

    cp "$ANDROID_BUILD_TOP/toolchain/gcc/gcc-4.9/COPYING" \
       "$NDK_DIR/$STL_DIR/$GNUSTL_DIR/NOTICE"
    FILES="$FILES $GNUSTL_DIR/NOTICE"

    PACKAGE="$PACKAGE_DIR/gnustl.zip"
    dump "Packaging: $PACKAGE"
    pack_archive "$PACKAGE" "$NDK_DIR/$STL_DIR" "$FILES"
    fail_panic "Could not package GNU libstdc++ binaries!"
fi

if [ -z "$OPTION_BUILD_DIR" ]; then
    log "Cleaning up..."
    rm -rf $BUILD_DIR
else
    log "Don't forget to cleanup: $BUILD_DIR"
fi

log "Done!"
