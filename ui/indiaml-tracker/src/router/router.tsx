import {
  createBrowserRouter,
  RouterProvider,
  useNavigate,
} from "react-router-dom";
import loadable from "@loadable/component";
import React, { useEffect } from "react";
// const Homepage = loadable(() => import("../views/Homepage"));

const V1Items = {
  V1Homepage: loadable(() => import("../v1/Homepage")),
  Landing: loadable(() => import("../v1/Landing")),
  Papers: loadable(() => import("../v1/papers")),
  About: loadable(() => import("../v1/about")),
  Motivation: loadable(() => import("../v1/motivation")),
  Analytics: loadable(() => import("../v1/conference-analytics")),
  AnalyticsV2: loadable(() => import("../v1/conference-analytics-new")),
  AnalyticsV3: loadable(() => import("../v1/conference-analytics-v3")),
  AnalyticsV4: loadable(() => import("../v1/dashboard-container"))
};

const AutoRedirectComponent = ({children}: {children: JSX.Element}) => {
  const navigate = useNavigate();
  useEffect(() => {
    if (window.location.pathname == '/') {
      navigate("/papers", { replace: true });
    }
  }, []);
  return children;
};

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AutoRedirectComponent children={<V1Items.V1Homepage />} />,
    children: [
      {
        path: "papers",
        element: <V1Items.Papers />,
      },
      {
        path: "analytics",
        element: <V1Items.Analytics />,
      },
      {
        path: "analytics-v2",
        element: <V1Items.AnalyticsV2 />,
      },
      {
        path: "analytics-v3",
        element: <V1Items.AnalyticsV3 />,
      },
      {
        path: "analytics-v4",
        element: <V1Items.AnalyticsV4 />,
      },
      {
        path: "landing",
        element: <V1Items.Landing />,
      },
      {
        path: "about",
        element: <V1Items.About />,
      },
      {
        path: "motivation",
        element: <V1Items.Motivation />,
      },
    ],
  },
]);
