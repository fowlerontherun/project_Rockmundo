import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface AvatarData {
  hair_color: string;
  top_clothing: string;
}

interface Props {
  avatar: AvatarData;
  onChange: (field: keyof AvatarData, value: string) => void;
}

const Designer: React.FC<Props> = ({ avatar, onChange }) => {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(300, 300);
    mount.appendChild(renderer.domElement);

    const geometry = new THREE.BoxGeometry();
    const material = new THREE.MeshBasicMaterial({ color: avatar.hair_color });
    const cube = new THREE.Mesh(geometry, material);
    scene.add(cube);
    camera.position.z = 5;

    const animate = () => {
      cube.rotation.x += 0.01;
      cube.rotation.y += 0.01;
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };
    animate();

    return () => {
      mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, [avatar.hair_color]);

  return (
    <div>
      <div ref={mountRef} />
      <div className="mt-2 space-y-2">
        <label className="block">
          Hair Color
          <input
            type="color"
            value={avatar.hair_color}
            onChange={(e) => onChange('hair_color', e.target.value)}
            className="ml-2"
          />
        </label>
        <label className="block">
          Top Clothing
          <input
            type="text"
            value={avatar.top_clothing}
            onChange={(e) => onChange('top_clothing', e.target.value)}
            className="ml-2 border"
          />
        </label>
      </div>
    </div>
  );
};

export default Designer;
