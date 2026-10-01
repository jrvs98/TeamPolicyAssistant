import Keycloak, { type KeycloakInstance } from "keycloak-js";

const keycloak: KeycloakInstance = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? "team-policy",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? "policy-web",
});

let initialization: Promise<boolean> | undefined;

export function initializeAuthentication(): Promise<boolean> {
  initialization ??= keycloak.init({
    onLoad: "check-sso",
    pkceMethod: "S256",
    checkLoginIframe: false,
  });
  return initialization;
}

export function login(): Promise<void> {
  return keycloak.login();
}

export function logout(): Promise<void> {
  return keycloak.logout({ redirectUri: window.location.origin });
}

export function getAccessToken(): string | undefined {
  return keycloak.token;
}

export function getUsername(): string | undefined {
  return keycloak.tokenParsed?.preferred_username;
}

export function getRoles(): string[] {
  return keycloak.tokenParsed?.realm_access?.roles ?? [];
}
