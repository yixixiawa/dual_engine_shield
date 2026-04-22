export { default } from './client'
export * from './client'
export * from './modules/phishing'
export * from './modules/vulnerability'
export * from './modules/health'
export * from './modules/ipinfo'
export { geoPhishingLocationsAPI, getGeoPhishingLocations } from './modules/geoPhishingLocations'
export type {
  GeoPhishingLocationEntity,
  GeoPhishingLocationsQuery,
  GeoPhishingLocationsResponse,
  GeoPhishingThreatLevel
} from './modules/geoPhishingLocations'
export * from "./modules/tasks"
