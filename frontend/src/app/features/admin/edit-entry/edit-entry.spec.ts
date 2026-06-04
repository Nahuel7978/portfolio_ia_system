import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EditEntry } from './edit-entry';

describe('EditEntry', () => {
  let component: EditEntry;
  let fixture: ComponentFixture<EditEntry>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EditEntry],
    }).compileComponents();

    fixture = TestBed.createComponent(EditEntry);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
