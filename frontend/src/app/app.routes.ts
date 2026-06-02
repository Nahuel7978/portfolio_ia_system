import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/home/home').then(m => m.HomeComponent) },
  { path: 'entry/:id', loadComponent: () => import('./features/detail/detail').then(m => m.DetailComponent) },
  { path: '**', redirectTo: '' }
];