// App.js
import React, { useRef, useState, useMemo } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Convert latitude & longitude (in degrees) to a Vector3 position on a sphere.
 * Here, the formula is adjusted so that the globe texture aligns well.
 * 
 * @param {number} lat - Latitude in degrees.
 * @param {number} lon - Longitude in degrees.
 * @param {number} radius - The sphere radius.
 * @param {number} [height=0] - Optional extra height (so markers “pop out”).
 * @returns {THREE.Vector3} - The computed position.
 */
function latLongToVector3(lat, lon, radius, height = 0) {
  // Convert degrees to radians.
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);

  const x = -(radius + height) * Math.sin(phi) * Math.cos(theta);
  const z = (radius + height) * Math.sin(phi) * Math.sin(theta);
  const y = (radius + height) * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

/**
 * RotatingGlobe renders a sphere with a night texture.
 * It uses a bump map to provide relief so that shading and 3D contours show,
 * even when most of the globe is dark.
 */
const RotatingGlobe = () => {
  const globeRef = useRef();

  // Load the night texture and a bump map for surface relief.
  const nightTexture = useLoader(
    THREE.TextureLoader,
    '/globetexture.jpg'
  );
  const bumpTexture = useLoader(
    THREE.TextureLoader,
    'earthbump4k.jpg'
  );

  // Slowly rotate the globe.
  useFrame(() => {
    if (globeRef.current) {
      globeRef.current.rotation.y += 0.001; // Adjust rotation speed as desired.
    }
  });

  return (
    <mesh ref={globeRef}>
      <sphereGeometry args={[2, 64, 64]} />
      <meshStandardMaterial
        map={nightTexture}
        bumpMap={bumpTexture}
        bumpScale={0.05} // Adjust bump scale to intensify the 3D relief.
        metalness={0.1}
        roughness={0.9}
      />
    </mesh>
  );
};

/**
 * Marker renders a small sphere at the given position.
 * It also handles pointer events to show/hide a tooltip.
 */
const Marker = ({ position, country, count, setTooltip }) => {
  return (
    <mesh
      position={position}
      onPointerOver={(e) => {
        // Stop event propagation so the globe beneath doesn't also capture the event.
        e.stopPropagation();
        // Set tooltip state with the country name and count.
        setTooltip({
          visible: true,
          x: e.clientX,
          y: e.clientY,
          content: `${country}: ${count} author${count > 1 ? 's' : ''}`,
        });
      }}
      onPointerOut={(e) => {
        e.stopPropagation();
        // Hide the tooltip when the pointer leaves.
        setTooltip({ visible: false, x: 0, y: 0, content: '' });
      }}
    >
      <sphereGeometry args={[0.05, 16, 16]} />
      {/* The emissive property helps the marker “glow” a bit against the dark globe */}
      <meshStandardMaterial color="red" emissive="red" />
    </mesh>
  );
};

/**
 * GlobeWithMarkers renders the globe and overlays markers for each country.
 * It groups the authors by country and uses a simple mapping (country code → lat/lon)
 * to determine where each marker goes.
 */
const GlobeWithMarkers = ({ authors, setTooltip }) => {
  // Group authors by country.
  const countryCounts = useMemo(() => {
    return authors.reduce((acc, { affiliation_country }) => {
      acc[affiliation_country] = (acc[affiliation_country] || 0) + 1;
      return acc;
    }, {});
  }, [authors]);

  // A simple mapping from country codes to approximate lat/lon.
  // (Adjust or extend these coordinates as needed.)
  const countryCoordinates = {
    GB: { lat: 55.3781, lon: -3.4360 },
    CA: { lat: 56.1304, lon: -106.3468 },
    US: { lat: 37.0902, lon: -95.7129 },
    CN: { lat: 35.8617, lon: 104.1954 },
  };

  return (
    <>
      <RotatingGlobe />
      {Object.entries(countryCounts).map(([country, count]) => {
        const coords = countryCoordinates[country];
        if (!coords) return null;
        // Calculate a position for the marker. The marker is placed slightly above the surface (height offset 0.1).
        const pos = latLongToVector3(coords.lat, coords.lon, 2, 0.1);
        return (
          <Marker
            key={country}
            position={pos}
            country={country}
            count={count}
            setTooltip={setTooltip}
          />
        );
      })}
    </>
  );
};

/**
 * App is the main component.
 * It maintains tooltip state and renders the Canvas and a tooltip overlay.
 */
const App = () => {
  // Tooltip state: visible flag, x/y position, and content.
  const [tooltip, setTooltip] = useState({
    visible: false,
    x: 0,
    y: 0,
    content: '',
  });

  // Example authors data.
  const authors = [
    { author_id: 2, full_name: 'Fabien Roger', openreview_id: '~Fabien_Roger1', affiliation_country: 'GB' },
    { author_id: 3, full_name: 'Dmitrii Krasheninnikov', openreview_id: '~Dmitrii_Krasheninnikov1', affiliation_country: 'GB' },
    { author_id: 4, full_name: 'David Krueger', openreview_id: '~David_Krueger1', affiliation_country: 'CA' },
    { author_id: 5, full_name: 'Jiamian Wang', openreview_id: '~Jiamian_Wang1', affiliation_country: 'US' },
    { author_id: 6, full_name: 'Yulun Zhang', openreview_id: '~Yulun_Zhang1', affiliation_country: 'CN' },
  ];

  return (
    <div style={{ position: 'relative', width: '100vw', height: '90vh' }}>
      {/* The Canvas provides the WebGL context. The background is set to black. */}
      <Canvas style={{ background: '#000' }} camera={{ position: [0, 0, 5] }}>
        {/* Ambient and directional lights enhance shading and depth. */}
        <ambientLight intensity={4} />
        <directionalLight position={[5, 3, 5]} intensity={1} />
        <GlobeWithMarkers authors={authors} setTooltip={setTooltip} />
      </Canvas>
      {/* Tooltip overlay, absolutely positioned on top of the Canvas. */}
      {tooltip.visible && (
        <div
          style={{
            position: 'absolute',
            top: tooltip.y + 10,
            left: tooltip.x + 10,
            background: 'rgba(0, 0, 0, 0.7)',
            color: '#fff',
            padding: '5px 10px',
            borderRadius: '4px',
            pointerEvents: 'none',
            whiteSpace: 'nowrap',
            fontSize: '12px',
          }}
        >
          {tooltip.content}
        </div>
      )}
    </div>
  );
};

export default App;
