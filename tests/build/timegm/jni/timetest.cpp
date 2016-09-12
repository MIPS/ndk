#include <time.h>

time_t timegm_wrapper(struct tm* t) {
    return timegm(t);
}

time_t timelocal_wrapper(struct tm* t) {
    return timelocal(t);
}
