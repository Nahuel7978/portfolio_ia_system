import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Technology } from '../models/technology.interface';

@Injectable({
  providedIn: 'root'
})
export class TechnologyService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/admin/technologies`;

  getTechnologies(): Observable<Technology[]> {
    return this.http.get<Technology[]>(this.apiUrl);
  }

  createTechnology(technology: Technology): Observable<Technology> {
    return this.http.post<Technology>(this.apiUrl, technology);
  }
}