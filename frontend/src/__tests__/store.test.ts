import { useStore } from "@/lib/store";

describe("Zustand Store", () => {
  beforeEach(() => {
    useStore.setState({
      url: "",
      isLoading: false,
      videoInfo: null,
      error: null,
      user: null,
      subscription: null,
    });
  });

  it("has correct initial state", () => {
    const state = useStore.getState();
    expect(state.url).toBe("");
    expect(state.isLoading).toBe(false);
    expect(state.videoInfo).toBeNull();
    expect(state.user).toBeNull();
  });

  it("sets URL correctly", () => {
    const { setUrl } = useStore.getState();
    setUrl("https://www.tiktok.com/@user/video/123456789");
    expect(useStore.getState().url).toBe("https://www.tiktok.com/@user/video/123456789");
  });

  it("sets loading state", () => {
    const { setIsLoading } = useStore.getState();
    setIsLoading(true);
    expect(useStore.getState().isLoading).toBe(true);
  });

  it("toggles dark mode", () => {
    const { toggleDarkMode } = useStore.getState();
    const initial = useStore.getState().isDarkMode;
    toggleDarkMode();
    expect(useStore.getState().isDarkMode).toBe(!initial);
  });

  it("adds recent URL", () => {
    const { addRecentUrl } = useStore.getState();
    addRecentUrl("https://test.com/video");
    expect(useStore.getState().recentUrls).toContain("https://test.com/video");
  });
});
