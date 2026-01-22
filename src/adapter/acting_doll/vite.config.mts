import { defineConfig, UserConfig, ConfigEnv } from 'vite';
import path from 'path';

export default defineConfig((env: ConfigEnv): UserConfig => {
  let common: UserConfig = {
    server: {
      port: 5000,
    },
    root: './',
    base: '/',
    publicDir: './../public',
    resolve: {
      extensions: ['.ts', '.js'],
      alias: {
        '@framework': path.resolve(__dirname, '../../Cubism/Framework/src'),
      }
    },
    build: {
      target: 'modules',
      assetsDir: 'assets',
      outDir: './dist',
      sourcemap: env.mode == 'development' ? true : false,
      rollupOptions: {
        input: {
          index: path.resolve(__dirname, 'index.html'),
          api: path.resolve(__dirname, 'API.html'),
        },
      },
    },
  };
  return common;
});
