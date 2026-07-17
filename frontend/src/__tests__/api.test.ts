import { api, loadTokens, clearTokens, getAuthToken } from "@/lib/api";

describe("API Client", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("loadTokens reads from localStorage", () => {
    localStorage.setItem("access_token", "test-access");
    localStorage.setItem("refresh_token", "test-refresh");
    loadTokens();
    expect(getAuthToken()).toBe("test-access");
  });

  it("clearTokens removes tokens", () => {
    localStorage.setItem("access_token", "test");
    clearTokens();
    expect(getAuthToken()).toBeNull();
  });

  it("getAuthToken returns null when no token", () => {
    expect(getAuthToken()).toBeNull();
  });
});
