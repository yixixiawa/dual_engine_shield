<template>
    <div class="earth-container">
        <div class="earth" id="container"></div>
    </div>
</template>

<script setup lang="ts">
import useEarthModel from "@/api/earth_model";
import { onMounted } from "vue";

const earthModel = useEarthModel();

onMounted(() => {
    // 初始化图表
    earthModel.initChart("container");
});
</script>

<style scoped>
.earth-container {
    width: 100%;
    height: 800px;
    position: relative;
}

.earth {
    width: 100%;
    height: 100%;
}
</style>