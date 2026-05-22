import { browser } from '$app/environment';
import { env as publicEnv } from '$env/dynamic/public';

/** Quando o browser acessa pela LAN, precisamos do host atual com porta do backend. */
function resolveApiUrl(): string {
  const fromEnv = publicEnv.PUBLIC_API_URL;
  if (browser && fromEnv && fromEnv.startsWith('http://localhost')) {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return fromEnv || 'http://localhost:8000';
}

function resolveTusdUrl(): string {
  const fromEnv = publicEnv.PUBLIC_TUSD_URL;
  if (browser && fromEnv && fromEnv.includes('localhost')) {
    return `${window.location.protocol}//${window.location.hostname}:1080/files/`;
  }
  return fromEnv || 'http://localhost:1080/files/';
}

export const API_URL = resolveApiUrl();
export const TUSD_URL = resolveTusdUrl();
