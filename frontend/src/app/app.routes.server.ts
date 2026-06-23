import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  {
    path: '',
    renderMode: RenderMode.Prerender,
  },
  {
    path: 'login',
    renderMode: RenderMode.Prerender,
  },
  {
    path: 'admin/technologies',
    renderMode: RenderMode.Prerender,
  },
  {
    path: 'admin/knowledge-entries',
    renderMode: RenderMode.Prerender,
  },
  {
    path: 'admin/new-entry',
    renderMode: RenderMode.Prerender,
  },
  //Dynamic
  { path: 'entry/:id',
    renderMode: RenderMode.Server,
  },
  { path: 'admin/edit-entry/:id',
    renderMode: RenderMode.Server,
  },
  // Fallback route
  {
    path: '**',
    renderMode: RenderMode.Server,
  },
];
