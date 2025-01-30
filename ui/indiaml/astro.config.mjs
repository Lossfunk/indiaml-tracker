// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
    integrations: [starlight({
        title: 'India@ML',
        social: {
            github: 'https://github.com/withastro/starlight',
        },
        sidebar: [
            {
                label: 'Accepted Papers by Indians',
                items: [
                    // Each item here is one entry in the navigation menu.
                    { label: 'NeurIPS 2024 Conference', slug: 'conferences/neurips-2024-conf' },
                    { label: 'ICML 2024 Conference', slug: 'conferences/icml-2024-conf' },
                ],
            },
            {
                label: 'Reference',
                autogenerate: { directory: 'reference' },
            },
        ],
		}), react()],
});