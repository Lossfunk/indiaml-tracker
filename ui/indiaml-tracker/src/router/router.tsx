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
  Motivation: loadable(() => import("../v1/motivation")),
  AnalyticsV4: loadable(() => import("../v1/conference-dashboard"))
};


const V2Items = {
  V2Homepage: loadable(() => import("../v2/Homepage")),
  Landing: loadable(() => import("../v2/Landing")),
  Papers: loadable(() => import("../v2/papers")),
  Motivation: loadable(() => import("../v2/motivation")),
  AnalyticsV4: loadable(() => import("../v2/conference-dashboard"))
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
        path: "conference-summary",
        element: <V1Items.AnalyticsV4 />,
      },
      {
        path: "landing",
        element: <V1Items.Landing />,
      },
      {
        path: "motivation",
        element: <V1Items.Motivation />,
      },
    ],
  },
    {
    path: "v2/",
    element: <AutoRedirectComponent children={<V2Items.V2Homepage />} />,
    children: [
      {
        path: "papers",
        element: <V2Items.Papers />,
      },
      {
        path: "conference-summary",
        element: <V2Items.AnalyticsV4 />,
      },
      {
        path: "landing",
        element: <V2Items.Landing />,
      },
      {
        path: "motivation",
        element: <V2Items.Motivation />,
      },
    ],
  },
]);
