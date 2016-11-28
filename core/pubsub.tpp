/// (c) Koheron

#ifndef __PUBSUB_TPP__
#define __PUBSUB_TPP__

#include "pubsub.hpp"
#include "kserver_session.hpp"

#if KSERVER_HAS_THREADS
#  include <thread>
#  include <mutex>
#endif

namespace kserver {

template<uint16_t channel, uint16_t event, typename... Tp>
inline void PubSub::emit(Tp&&... args)
{
    static_assert(channel < channels_count, "Invalid channel");

    for (auto const& sid : subscribers.get(channel))
        session_manager.get_session(sid).send<channel, event>(
            std::make_tuple(std::forward<Tp>(args)...)
        );
}

template<uint16_t channel, uint16_t event>
inline void PubSub::emit_cstr(const char *str)
{
    static_assert(channel < channels_count, "Invalid channel");

    if (subscribers.count(channel) > 0) {
        for (auto const& sid : subscribers.get(channel))
            session_manager.get_session(sid).send<channel, event>(str);
    }
}

} // namespace kserver

#endif // __PUBSUB_TPP__
