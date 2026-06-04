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
      { path: 'dashboard', loadComponent: () => import('./features/admin/dashboard/dashboard').then(m => m.DashboardComponent) },
      { path: 'technologies', loadComponent: () => import('./features/admin/technology/technology').then(m => m.TechnologiesComponent)}
    ]
  },
  { path: '**', redirectTo: '' }
];