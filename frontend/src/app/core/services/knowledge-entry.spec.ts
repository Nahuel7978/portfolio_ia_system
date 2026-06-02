import { TestBed } from '@angular/core/testing';

import { KnowledgeEntry } from './knowledge-entry';

describe('KnowledgeEntry', () => {
  let service: KnowledgeEntry;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(KnowledgeEntry);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
