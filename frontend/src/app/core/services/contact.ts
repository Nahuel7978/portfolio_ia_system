import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

// Tipado estricto para el payload
export interface ContactPayload {
  name: string;
  email: string;
  subject: string;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ContactService {
  // Inyección de dependencias moderna (Angular 14+)
  private http = inject(HttpClient);
  
  // Construcción de la URL basada en los environments
  private apiUrl = `${environment.apiUrl}/public/contact`;

  /**
   * Envía los datos del formulario al Web Core.
   * Retorna un Observable al que el componente debe suscribirse.
   */
  sendMessage(data: ContactPayload): Observable<any> {
    return this.http.post(this.apiUrl, data);
  }
}