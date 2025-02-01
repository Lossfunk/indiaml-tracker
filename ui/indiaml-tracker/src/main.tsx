import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { ThemeProvider } from "@/components/theme-provider";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { router } from "@/router/router";
import { TopNav } from "./v1/top-nav";


ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
    <React.StrictMode>
      <div className="w-full h-[100dvh] touch-manipulation select-none">
        <RouterProvider router={router} />
      </div>
    </React.StrictMode>
  </ThemeProvider>
);
