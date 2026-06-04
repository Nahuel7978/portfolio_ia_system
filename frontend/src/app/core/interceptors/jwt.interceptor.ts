import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  // Solo inyectamos el token si la ruta es de administración
  let clonedRequest = req;
  if (token && req.url.includes('/admin/')) {
    clonedRequest = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  return next(clonedRequest).pipe(
    catchError((error: HttpErrorResponse) => {
      // Si el backend nos dice que no estamos autorizados (token expirado o inválido)
      if (error.status === 401) {
        authService.logout();
      }
      return throwError(() => error);
    })
  );
};