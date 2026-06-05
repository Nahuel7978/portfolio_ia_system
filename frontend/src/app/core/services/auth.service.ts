import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment.development';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);
  private readonly TOKEN_KEY = 'portfolio_admin_jwt';
  private authStatusSource = new BehaviorSubject<boolean>(false);
  // 3. Exponerlo como Observable para que los componentes se suscriban
  public authStatus$ = this.authStatusSource.asObservable();

  constructor() {
    // 4. Al arrancar el servicio, revisar si ya había un token guardado (seguro para SSR)
    if (isPlatformBrowser(this.platformId)) {
      this.authStatusSource.next(!!localStorage.getItem(this.TOKEN_KEY));
    }
  }

  login(credentials: { username: string; password: string }) {
    return this.http.post<{ token: string }>(`${environment.apiUrl}/auth/login`, credentials).pipe(
      tap(response => this.setToken(response.token))
    );
  }

  logout() {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.removeItem(this.TOKEN_KEY);
      this.authStatusSource.next(false);
    }
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    if (isPlatformBrowser(this.platformId)) {
      return localStorage.getItem(this.TOKEN_KEY);
    }
    return null;
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private setToken(token: string) {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem(this.TOKEN_KEY, token);
      this.authStatusSource.next(true);
    }
  }
}