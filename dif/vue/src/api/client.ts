import { createAlova } from "alova"
import GlobalFetch from "alova/fetch"

export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api"
export const DEFAULT_TIMEOUT = 300000

const alovaInstance = createAlova({
    requestAdapter: GlobalFetch(),
    baseURL: API_BASE,
    timeout: DEFAULT_TIMEOUT
})

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

type JsonObject = Record<string, unknown>

const buildUrl = (path: string, query?: JsonObject) => {
    const normalizedPath = path.startsWith("/") ? path : `/${path}`
    const url = new URL(`${API_BASE}${normalizedPath}`)

    if (query) {
        Object.entries(query).forEach(([key, value]) => {
            if (value === undefined || value === null) return

            if (Array.isArray(value)) {
                value.forEach((item) => url.searchParams.append(key, String(item)))
                return
            }

            url.searchParams.set(key, String(value))
        })
    }

    return url.toString()
}

const parseResponse = async (response: Response) => {
    const contentType = response.headers.get("content-type") || ""

    if (contentType.includes("application/json")) {
        return response.json()
    }

    const text = await response.text()
    return text ? { message: text } : {}
}

export async function apiCall<T = unknown>(
    path: string,
    method: HttpMethod = "GET",
    payload?: unknown,
    timeout = DEFAULT_TIMEOUT
): Promise<T> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
        const isGet = method === "GET"
        const query = isGet && payload && typeof payload === "object" ? (payload as JsonObject) : undefined
        const headers: HeadersInit | undefined = isGet ? undefined : { "Content-Type": "application/json" }
        const response = await fetch(buildUrl(path, query), {
            method,
            headers,
            credentials: "include",
            signal: controller.signal,
            body: isGet ? undefined : JSON.stringify(payload ?? {})
        })

        const data = await parseResponse(response)

        if (!response.ok) {
            const message =
                (data as JsonObject)?.error ||
                (data as JsonObject)?.message ||
                `请求失败 (${response.status})`
            throw new Error(String(message))
        }

        return data as T
    } catch (error) {
        if ((error as Error).name === "AbortError") {
            throw new Error("请求超时，请稍后重试")
        }
        throw error
    } finally {
        clearTimeout(timeoutId)
    }
}

export default alovaInstance
