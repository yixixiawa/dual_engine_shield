import { apiCall } from "../client";

/**
 * 任务接口
 */
export interface Task {
    id: number;
    task_id: number;
    status: string;
    input_data: string;
    processing_time_ms: number | null;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

/**
 * 任务列表响应
 */
export interface TaskListResponse {
    count: number
    next: string | null
    previous: string | null
    results: Task[]
}

/**
 * 任务详情响应
 */
export interface TaskDetailResponse {
    task_id: number;
    task_status: string;
    detection_type: string;
    input_data: string;
    result: any;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

/**
 * 获取任务列表
 *
 * @param params 查询参数
 * @returns 任务列表
 */
export async function getTaskList(params?: {
    page?: number;
    limit?: number;
    page_size?: number;
    type?: string;
    status?: string;
}): Promise<TaskListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    // 优先使用page_size参数，兼容limit参数
    const pageSize = params?.page_size || params?.limit;
    if (pageSize) queryParams.append('page_size', pageSize.toString());
    if (params?.type) queryParams.append('type', params.type);
    if (params?.status) queryParams.append('status', params.status);

    const queryString = queryParams.toString();
    const url = `/detection-logs/${queryString ? `?${queryString}` : ''}`;

    return await apiCall(url, 'GET');
}

/**
 * 获取任务详情
 *
 * @param taskId 任务ID
 * @returns 任务详情
 */
export async function getTaskDetail(taskId: number): Promise<TaskDetailResponse> {
    return await apiCall(`/detect/fish-task/${taskId}/`, 'GET');
}

/**
 * 删除任务
 *
 * @param taskId 任务ID
 * @returns 删除结果
 */
export async function deleteTask(taskId: number): Promise<{
    status: string;
    message: string;
}> {
    return await apiCall(`/detect/fish-task/${taskId}/`, 'DELETE');
}