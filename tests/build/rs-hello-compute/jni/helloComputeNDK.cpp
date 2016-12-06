/*
 * Copyright (C) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <jni.h>
#include <android/log.h>
#include <android/bitmap.h>

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "RenderScript.h"

#include "ScriptC_mono.h"

#define  LOG_TAG    "HelloComputeNDK"
#define  LOGI(...)  __android_log_print(ANDROID_LOG_INFO,LOG_TAG,__VA_ARGS__)
#define  LOGE(...)  __android_log_print(ANDROID_LOG_ERROR,LOG_TAG,__VA_ARGS__)

using namespace android::RSC;

extern "C" JNIEXPORT void JNICALL
Java_com_example_android_rs_hellocomputendk_HelloComputeNDK_nativeMono(JNIEnv * env,
                                                                       jclass,
                                                                       jstring pathObj,
                                                                       jint X,
                                                                       jint Y,
                                                                       jobject jbitmapIn,
                                                                       jobject jbitmapOut
                                                                       )
{
    void* inputPtr = nullptr;
    void* outputPtr = nullptr;

    AndroidBitmap_lockPixels(env, jbitmapIn, &inputPtr);
    AndroidBitmap_lockPixels(env, jbitmapOut, &outputPtr);

    const char * path = env->GetStringUTFChars(pathObj, nullptr);
    sp<RS> rs = new RS();
    rs->init(path);
    env->ReleaseStringUTFChars(pathObj, path);

    sp<const Element> e = Element::RGBA_8888(rs);

    sp<const Type> t = Type::create(rs, e, X, Y, 0);

    sp<Allocation> inputAlloc = Allocation::createTyped(rs, t, RS_ALLOCATION_MIPMAP_NONE,
                                                        RS_ALLOCATION_USAGE_SHARED | RS_ALLOCATION_USAGE_SCRIPT,
                                                        inputPtr);
    sp<Allocation> outputAlloc = Allocation::createTyped(rs, t, RS_ALLOCATION_MIPMAP_NONE,
                                                         RS_ALLOCATION_USAGE_SHARED | RS_ALLOCATION_USAGE_SCRIPT,
                                                         outputPtr);


    inputAlloc->copy2DRangeFrom(0, 0, X, Y, inputPtr);
    ScriptC_mono* sc = new ScriptC_mono(rs);
    sc->forEach_root(inputAlloc, outputAlloc);
    outputAlloc->copy2DRangeTo(0, 0, X, Y, outputPtr);

    AndroidBitmap_unlockPixels(env, jbitmapIn);
    AndroidBitmap_unlockPixels(env, jbitmapOut);

}
