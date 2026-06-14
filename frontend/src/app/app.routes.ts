import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/home/home').then(m => m.HomeComponent) },
  { path: 'entry/:id', loadComponent: () => import('./features/detail/detail').then(m => m.DetailComponent) },
  { path: 'login', loadComponent: () => import('./features/admin/login/login').then(m => m.LoginComponent) },
  { 
    path: 'admin', 
    canActivate: [authGuard], // <-- Guardián protegiendo todo el módulo admin
    children: [
      { path: 'technologies', loadComponent: () => import('./features/admin/technology/technology').then(m => m.TechnologiesComponent)},
      { path: 'knowledge-entries', loadComponent: () => import('./features/admin/knowledge-entries/knowledge-entries').then(m => m.KnowledgeEntriesComponent)},
      { path: 'new-entry', loadComponent: () => import('./features/admin/entries-form/entries-form').then(m => m.EntryFormComponent)},
      { path: 'edit-entry/:id', loadComponent: () => import('./features/admin/edit-entry/edit-entry').then(m => m.EditEntryComponent)}
    ]
  },
  { path: '**', redirectTo: '' }
];