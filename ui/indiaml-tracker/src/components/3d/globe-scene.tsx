// RotatingGlobe.js
import React, { useRef } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import * as THREE from 'three';

const RotatingGlobe = () => {
  const globeRef = useRef();

  // Load an Earth texture (feel free to replace with your own image URL)
  const texture = useLoader(
    THREE.TextureLoader,
    '/globetexture.jpg'
  );

  // Slowly rotate the globe on each frame
  useFrame(() => {
    if (globeRef.current) {
      globeRef.current.rotation.y += 0.0005; // Adjust the speed as needed
    }
  });

  return (
    <mesh ref={globeRef}>
      <sphereGeometry args={[2, 32, 32]} />
      <meshStandardMaterial map={texture} />
    </mesh>
  );
};

const GlobeScene = () => (
  <Canvas camera={{ position: [0, 0, 5] }}>
    <ambientLight intensity={2} />
    <pointLight position={[10, 10, 10]} />
    <RotatingGlobe />
  </Canvas>
);

export default GlobeScene;
