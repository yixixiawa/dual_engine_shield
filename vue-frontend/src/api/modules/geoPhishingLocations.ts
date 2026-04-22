import { apiCall } from '../client'

export type GeoPhishingThreatLevel = 'safe' | 'suspicious' | 'phishing' | 'malware' | 'unknown'

export interface GeoPhishingLocationEntity {
  id: number | null
  ip_address: string
  domain?: string | null
  country?: string | null
  city?: string | null
  latitude: number | null
  longitude: number | null
  threat_level: GeoPhishingThreatLevel
  is_phishing: boolean
  risk_score: number
  last_seen?: string | null
  query_count?: number
  status?: string
}

export interface GeoPhishingLocationsQuery {
  country?: string
  city?: string
  status?: string
  page?: number
  page_size?: number
}

export interface GeoPhishingLocationsResponse {
  status: string
  source?: string
  count: number
  page: number
  page_size: number
  data: GeoPhishingLocationEntity[]
}

export const geoPhishingLocationsAPI = {
  async list(params?: GeoPhishingLocationsQuery): Promise<GeoPhishingLocationsResponse> {
    return apiCall<GeoPhishingLocationsResponse>('/geo-phishing/locations/', 'GET', params)
  }
}

export const getGeoPhishingLocations = geoPhishingLocationsAPI.list
