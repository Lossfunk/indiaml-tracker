import {
  createBrowserRouter,
  RouterProvider,
  useNavigate,
} from "react-router-dom";
import loadable from "@loadable/component";
import React, { useEffect } from "react";
// const Homepage = loadable(() => import("../views/Homepage"));

const V1Urls = {
  V2Homepage: loadable(() => import("../v1/Homepage")),
  NeurIPS2024: loadable(() => import("../v1/neurips-2024")),
};

const AutoRedirectComponent = ({children}: {children: JSX.Element}) => {
  const navigate = useNavigate();
  useEffect(() => {
    navigate("/papers-2024", { replace: true });
  }, []);
  return children;
};

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AutoRedirectComponent children={<V1Urls.V2Homepage />} />,
    children: [
      {
        path: "papers-2024",
        element: <V1Urls.NeurIPS2024 />,
      },
    ],
  },
]);
