// gpu_raster_compute.cpp -- minimal Vulkan compute host: dispatch
// gpu_raster.comp over a width x height grid for one triangle, print
// every covered pixel as "COV x y" (same format
// test_gpu_raster_oracle_rtl_parity.py's RTL scan already uses, so the
// Python side can parse both the same way).
//
// argv: a0 b0 c0 a1 b1 c1 a2 b2 c2 width height shader_spv_path
//
// Deliberately minimal for a one-shot utility, not a real-time
// renderer: no validation layers, no staging buffer (a single
// host-visible+coherent storage buffer is written directly by the
// shader and read back after a single dispatch+wait), no swapchain.
#include <vulkan/vulkan.h>

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <vector>

struct PushConstants {
    int32_t a0, b0, c0;
    int32_t a1, b1, c1;
    int32_t a2, b2, c2;
    int32_t width, height;
};

static void check(VkResult r, const char *what) {
    if (r != VK_SUCCESS) {
        std::fprintf(stderr, "Vulkan error %d in %s\n", (int)r, what);
        std::exit(1);
    }
}

static std::vector<uint32_t> readSpirv(const char *path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("cannot open SPIR-V file");
    size_t size = (size_t)f.tellg();
    f.seekg(0);
    std::vector<uint32_t> code(size / sizeof(uint32_t));
    f.read(reinterpret_cast<char *>(code.data()), (std::streamsize)size);
    return code;
}

static uint32_t findComputeQueueFamily(VkPhysicalDevice pd) {
    uint32_t count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(pd, &count, nullptr);
    std::vector<VkQueueFamilyProperties> props(count);
    vkGetPhysicalDeviceQueueFamilyProperties(pd, &count, props.data());
    for (uint32_t i = 0; i < count; i++)
        if (props[i].queueFlags & VK_QUEUE_COMPUTE_BIT) return i;
    std::fprintf(stderr, "no compute queue family found\n");
    std::exit(1);
}

static uint32_t findMemoryType(VkPhysicalDevice pd, uint32_t typeBits,
                                VkMemoryPropertyFlags want) {
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(pd, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++) {
        if ((typeBits & (1u << i)) &&
            (mp.memoryTypes[i].propertyFlags & want) == want)
            return i;
    }
    std::fprintf(stderr, "no suitable memory type\n");
    std::exit(1);
}

int main(int argc, char **argv) {
    if (argc != 13) {
        std::fprintf(stderr,
            "usage: %s a0 b0 c0 a1 b1 c1 a2 b2 c2 width height shader.spv\n",
            argv[0]);
        return 2;
    }
    PushConstants pc{};
    pc.a0 = std::atoi(argv[1]);  pc.b0 = std::atoi(argv[2]);  pc.c0 = std::atoi(argv[3]);
    pc.a1 = std::atoi(argv[4]);  pc.b1 = std::atoi(argv[5]);  pc.c1 = std::atoi(argv[6]);
    pc.a2 = std::atoi(argv[7]);  pc.b2 = std::atoi(argv[8]);  pc.c2 = std::atoi(argv[9]);
    pc.width = std::atoi(argv[10]);
    pc.height = std::atoi(argv[11]);
    const char *shaderPath = argv[12];

    const uint32_t width = (uint32_t)pc.width, height = (uint32_t)pc.height;
    const VkDeviceSize bufSize = (VkDeviceSize)width * height * sizeof(uint32_t);

    // -- Instance (headless compute, no validation/extensions needed) --
    VkApplicationInfo appInfo{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    appInfo.pApplicationName = "gpu_raster_compute";
    appInfo.apiVersion = VK_API_VERSION_1_2;
    VkInstanceCreateInfo instInfo{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    instInfo.pApplicationInfo = &appInfo;
    VkInstance instance;
    check(vkCreateInstance(&instInfo, nullptr, &instance), "vkCreateInstance");

    uint32_t pdCount = 0;
    vkEnumeratePhysicalDevices(instance, &pdCount, nullptr);
    if (pdCount == 0) { std::fprintf(stderr, "no Vulkan physical devices\n"); return 1; }
    std::vector<VkPhysicalDevice> pds(pdCount);
    vkEnumeratePhysicalDevices(instance, &pdCount, pds.data());
    VkPhysicalDevice pd = pds[0];  // first device is sufficient for this utility

    uint32_t qFamily = findComputeQueueFamily(pd);
    float qPriority = 1.0f;
    VkDeviceQueueCreateInfo qInfo{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    qInfo.queueFamilyIndex = qFamily;
    qInfo.queueCount = 1;
    qInfo.pQueuePriorities = &qPriority;

    VkDeviceCreateInfo devInfo{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    devInfo.queueCreateInfoCount = 1;
    devInfo.pQueueCreateInfos = &qInfo;
    VkDevice device;
    check(vkCreateDevice(pd, &devInfo, nullptr, &device), "vkCreateDevice");
    VkQueue queue;
    vkGetDeviceQueue(device, qFamily, 0, &queue);

    // -- Storage buffer, host-visible+coherent (one-shot utility: skip
    //    the staging-buffer + device-local-copy path a real renderer
    //    would use) --
    VkBufferCreateInfo bufInfo{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    bufInfo.size = bufSize;
    bufInfo.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
    bufInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    VkBuffer buffer;
    check(vkCreateBuffer(device, &bufInfo, nullptr, &buffer), "vkCreateBuffer");

    VkMemoryRequirements memReq;
    vkGetBufferMemoryRequirements(device, buffer, &memReq);
    VkMemoryAllocateInfo allocInfo{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    allocInfo.allocationSize = memReq.size;
    allocInfo.memoryTypeIndex = findMemoryType(
        pd, memReq.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    VkDeviceMemory memory;
    check(vkAllocateMemory(device, &allocInfo, nullptr, &memory), "vkAllocateMemory");
    check(vkBindBufferMemory(device, buffer, memory, 0), "vkBindBufferMemory");

    // -- Shader module + descriptor/pipeline layout --
    auto spirv = readSpirv(shaderPath);
    VkShaderModuleCreateInfo shaderInfo{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
    shaderInfo.codeSize = spirv.size() * sizeof(uint32_t);
    shaderInfo.pCode = spirv.data();
    VkShaderModule shaderModule;
    check(vkCreateShaderModule(device, &shaderInfo, nullptr, &shaderModule),
          "vkCreateShaderModule");

    VkDescriptorSetLayoutBinding binding{};
    binding.binding = 0;
    binding.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    binding.descriptorCount = 1;
    binding.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    VkDescriptorSetLayoutCreateInfo dsLayoutInfo{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    dsLayoutInfo.bindingCount = 1;
    dsLayoutInfo.pBindings = &binding;
    VkDescriptorSetLayout dsLayout;
    check(vkCreateDescriptorSetLayout(device, &dsLayoutInfo, nullptr, &dsLayout),
          "vkCreateDescriptorSetLayout");

    VkPushConstantRange pcRange{};
    pcRange.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    pcRange.offset = 0;
    pcRange.size = sizeof(PushConstants);
    VkPipelineLayoutCreateInfo plInfo{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    plInfo.setLayoutCount = 1;
    plInfo.pSetLayouts = &dsLayout;
    plInfo.pushConstantRangeCount = 1;
    plInfo.pPushConstantRanges = &pcRange;
    VkPipelineLayout pipelineLayout;
    check(vkCreatePipelineLayout(device, &plInfo, nullptr, &pipelineLayout),
          "vkCreatePipelineLayout");

    VkPipelineShaderStageCreateInfo stageInfo{
        VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};
    stageInfo.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    stageInfo.module = shaderModule;
    stageInfo.pName = "main";
    VkComputePipelineCreateInfo pipeInfo{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
    pipeInfo.stage = stageInfo;
    pipeInfo.layout = pipelineLayout;
    VkPipeline pipeline;
    check(vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &pipeInfo, nullptr,
                                    &pipeline),
          "vkCreateComputePipelines");

    // -- Descriptor pool/set, bind the buffer --
    VkDescriptorPoolSize poolSize{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1};
    VkDescriptorPoolCreateInfo poolInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    poolInfo.maxSets = 1;
    poolInfo.poolSizeCount = 1;
    poolInfo.pPoolSizes = &poolSize;
    VkDescriptorPool descPool;
    check(vkCreateDescriptorPool(device, &poolInfo, nullptr, &descPool),
          "vkCreateDescriptorPool");

    VkDescriptorSetAllocateInfo dsAllocInfo{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    dsAllocInfo.descriptorPool = descPool;
    dsAllocInfo.descriptorSetCount = 1;
    dsAllocInfo.pSetLayouts = &dsLayout;
    VkDescriptorSet descSet;
    check(vkAllocateDescriptorSets(device, &dsAllocInfo, &descSet),
          "vkAllocateDescriptorSets");

    VkDescriptorBufferInfo dbInfo{buffer, 0, bufSize};
    VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
    write.dstSet = descSet;
    write.dstBinding = 0;
    write.descriptorCount = 1;
    write.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    write.pBufferInfo = &dbInfo;
    vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);

    // -- Command buffer: bind, push constants, dispatch --
    VkCommandPoolCreateInfo cmdPoolInfo{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    cmdPoolInfo.queueFamilyIndex = qFamily;
    VkCommandPool cmdPool;
    check(vkCreateCommandPool(device, &cmdPoolInfo, nullptr, &cmdPool),
          "vkCreateCommandPool");

    VkCommandBufferAllocateInfo cbAllocInfo{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cbAllocInfo.commandPool = cmdPool;
    cbAllocInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cbAllocInfo.commandBufferCount = 1;
    VkCommandBuffer cmd;
    check(vkAllocateCommandBuffers(device, &cbAllocInfo, &cmd),
          "vkAllocateCommandBuffers");

    VkCommandBufferBeginInfo beginInfo{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    beginInfo.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    check(vkBeginCommandBuffer(cmd, &beginInfo), "vkBeginCommandBuffer");
    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline);
    vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipelineLayout, 0,
                             1, &descSet, 0, nullptr);
    vkCmdPushConstants(cmd, pipelineLayout, VK_SHADER_STAGE_COMPUTE_BIT, 0,
                        sizeof(PushConstants), &pc);
    uint32_t gx = (width + 15) / 16, gy = (height + 15) / 16;
    vkCmdDispatch(cmd, gx, gy, 1);
    check(vkEndCommandBuffer(cmd), "vkEndCommandBuffer");

    VkSubmitInfo submitInfo{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    submitInfo.commandBufferCount = 1;
    submitInfo.pCommandBuffers = &cmd;
    check(vkQueueSubmit(queue, 1, &submitInfo, VK_NULL_HANDLE), "vkQueueSubmit");
    check(vkQueueWaitIdle(queue), "vkQueueWaitIdle");

    // -- Read back and report every covered pixel --
    void *mapped;
    check(vkMapMemory(device, memory, 0, bufSize, 0, &mapped), "vkMapMemory");
    const uint32_t *cov = reinterpret_cast<const uint32_t *>(mapped);
    for (uint32_t y = 0; y < height; y++)
        for (uint32_t x = 0; x < width; x++)
            if (cov[y * width + x])
                std::printf("COV %u %u\n", x, y);
    vkUnmapMemory(device, memory);
    std::printf("SCAN DONE\n");

    vkDestroyCommandPool(device, cmdPool, nullptr);
    vkDestroyDescriptorPool(device, descPool, nullptr);
    vkDestroyPipeline(device, pipeline, nullptr);
    vkDestroyPipelineLayout(device, pipelineLayout, nullptr);
    vkDestroyDescriptorSetLayout(device, dsLayout, nullptr);
    vkDestroyShaderModule(device, shaderModule, nullptr);
    vkFreeMemory(device, memory, nullptr);
    vkDestroyBuffer(device, buffer, nullptr);
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);
    return 0;
}
