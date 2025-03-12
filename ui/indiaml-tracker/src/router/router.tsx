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
  NeurIPS2024: loadable(() => import("../v1/neurips-2024")),
  Maps2024: loadable(() => import("../v1/cc-map")),
  About: loadable(() => import("../v1/about")),
  Motivation: loadable(() => import("../v1/motivation")),
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
        path: "papers-2024",
        element: <V1Items.NeurIPS2024 />,
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
      {
        path: "map-2024",
        element: <V1Items.Maps2024 />,
      },
    ],
  },
]);
