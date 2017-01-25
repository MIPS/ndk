#include <jni.h>
#include <string>

#include <android/log.h>

extern "C"
JNIEXPORT jstring JNICALL
Java_com_example_myapplication_MainActivity_stringFromJNI(
        JNIEnv *env,
        jobject /* this */) {
    std::string hello = "Hello from C++";
    __android_log_print(ANDROID_LOG_INFO, "tag", "%s", hello.c_str());
    return env->NewStringUTF(hello.c_str());
}
