import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Features from "@/components/Features";

describe("Features", () => {
  it("renders features section", () => {
    render(<Features />);
    expect(screen.getByText("11+ Platforms")).toBeInTheDocument();
    expect(screen.getByText("Lightning Fast")).toBeInTheDocument();
    expect(screen.getByText("Secure & Private")).toBeInTheDocument();
  });

  it("renders feature descriptions", () => {
    render(<Features />);
    expect(screen.getByText(/YouTube, TikTok, Instagram, Twitter, Facebook/)).toBeInTheDocument();
    expect(screen.getByText(/We never store your data/)).toBeInTheDocument();
  });
});
