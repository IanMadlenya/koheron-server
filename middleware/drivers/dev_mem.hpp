/// Device memory manager
///
/// (c) Koheron

#ifndef __DRIVERS_CORE_DEV_MEM_HPP__
#define __DRIVERS_CORE_DEV_MEM_HPP__

#include <map>
#include <vector>
#include <array>
#include <cstdint>
#include <string>
#include <assert.h> 

extern "C" {
    #include <fcntl.h>
}

#include "memory_map.hpp"

/// @namespace Klib
/// @brief Namespace of the Koheron library
namespace Klib {

struct MemoryRegion
{
    uintptr_t phys_addr;
    uint32_t range;
};

/// ID of a memory map
typedef uint32_t MemMapID;

class MemMapIdPool
{
  public:
    MemMapIdPool() : reusable_ids(0) {};

    MemMapID get_id(unsigned int num_maps);
    void release_id(MemMapID id);
  private:
    std::vector<MemMapID> reusable_ids;
};

/// Device memory manager
/// A memory maps factory
class DevMem
{
  public:
    DevMem(uintptr_t addr_limit_down_=0x0, uintptr_t addr_limit_up_=0x0);
    ~DevMem();

    /// Open the /dev/mem driver
    int Open();
	
    /// Close all the memory maps
    /// @return 0 if succeed, -1 else
    int Close();

    /// Current number of memory maps
    static unsigned int num_maps;

    template<size_t N>
    std::array<MemMapID, N> 
    RequestMemoryMaps(std::array<MemoryRegion, N> regions);

    // Helper function to check the IDs returned by RequestMemoryMaps
    template<size_t N>
    int CheckMapIDs(std::array<MemMapID, N> ids);

    int Resize(MemMapID id, uint32_t length);

    /// Create a new memory map
    /// @addr Base address of the map
    /// @size Size of the map 
    /// @return An ID to the created map,
    ///         or -1 if an error occured
    MemMapID AddMemoryMap(uintptr_t addr, uint32_t size);
    
    /// Remove a memory map
    /// @id ID of the memory map to be removed
    void RmMemoryMap(MemMapID id);
    
    /// Remove all the memory maps
    void RemoveAll();
    
    /// Get a memory map
    /// @id ID of the memory map
    MemoryMap& GetMemMap(MemMapID id);
    
    /// Return the base address of a map
    /// @id ID of the map
    uintptr_t GetBaseAddr(MemMapID id);
    
    /// Return the status of a map
    /// @id ID of the map
    int GetStatus(MemMapID id);
	
    /// Return 1 if a memory map failed
    int IsFailed();
    
    /// True if the /dev/mem device is open
    inline bool IsOpen() const {return is_open;}

  private:
    int fd;         ///< /dev/mem file ID
    bool is_open;   ///< True if /dev/mem open
    
    /// Limit addresses
    uintptr_t addr_limit_down;
    uintptr_t addr_limit_up;
    bool __is_forbidden_address(uintptr_t addr);

    std::map<MemMapID, MemoryMap*> mem_maps;
    MemMapIdPool id_pool;
};

// Helper to build an std::array of memmory regions without
// specifying the length. Called as:
// mem_regions(
//     Klib::MemoryRegion({ ADDR1, RANGE1 }),
//     ...
//     Klib::MemoryRegion({ ADDRn, RANGEn })
// )
template<typename... region>
constexpr auto mem_regions(region&&... args) 
    -> std::array<Klib::MemoryRegion, sizeof...(args)>
{
    return {{std::forward<region>(args)...}};
}

template<size_t N>
std::array<MemMapID, N> 
DevMem::RequestMemoryMaps(std::array<MemoryRegion, N> regions)
{
    auto map_ids = std::array<MemMapID, N>();
    map_ids.fill(static_cast<MemMapID>(-1));
    uint32_t i = 0;

    for (auto& region : regions) {
        for (auto& mem_map : mem_maps) {
            if (region.phys_addr == mem_map.second->PhysAddr()) {
                // we resize the map if the new range is large
                // than the previously allocated one.
                if (region.range > mem_map.second->MappedSize())
                    if (Resize(mem_map.first, region.range) < 0)
                        fprintf(stderr, "Memory map resizing failed\n"); // How should we handle this error ?

                map_ids[i] = mem_map.first;
                break;
            }
        }

        if (static_cast<int>(map_ids[i]) < 0) // The required region is not mapped
            map_ids[i] = AddMemoryMap(region.phys_addr, region.range);

        i++;
    }

    return map_ids;
}

template<size_t N>
int DevMem::CheckMapIDs(std::array<MemMapID, N> ids)
{
    for (auto& id : ids)
        if (static_cast<int>(id) < 0)
            return -1;

    return 0;
}

}; // namespace Klib

#endif // __DRIVERS_CORE_DEV_MEM_HPP__
