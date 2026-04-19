import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface WhitelistItem {
    domain: string
    isSystem: boolean
}

export const useWhitelistStore = defineStore('whitelist', () => {
    const panelVisible = ref(false)
    const whitelist = ref<WhitelistItem[]>([
        { domain: 'gdust.edu.cn', isSystem: true },
        { domain: '*.edu.cn', isSystem: true }
    ])
    const eduForceReduce = ref(true)

    const togglePanel = () => {
        panelVisible.value = !panelVisible.value
    }

    const addWhitelist = (domain: string) => {
        if (!whitelist.value.some(item => item.domain === domain)) {
            whitelist.value.push({ domain, isSystem: false })
        }
    }

    const removeWhitelist = (domain: string) => {
        const index = whitelist.value.findIndex(item => item.domain === domain)
        if (index !== -1 && !whitelist.value[index].isSystem) {
            whitelist.value.splice(index, 1)
        }
    }

    const isWhitelisted = (url: string): boolean => {
        // 实现白名单匹配逻辑
        return whitelist.value.some(item => {
            if (item.domain.includes('*')) {
                const pattern = item.domain.replace(/\./g, '\\.').replace(/\*/g, '.*')
                return new RegExp(pattern).test(url)
            }
            return url.includes(item.domain)
        })
    }

    return {
        panelVisible,
        whitelist,
        eduForceReduce,
        togglePanel,
        addWhitelist,
        removeWhitelist,
        isWhitelisted
    }
})