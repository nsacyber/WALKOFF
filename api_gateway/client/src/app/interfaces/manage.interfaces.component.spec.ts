import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageInterfacesComponent } from './manage.interfaces.component';

describe('ManageInterfacesComponent', () => {
  let component: ManageInterfacesComponent;
  let fixture: ComponentFixture<ManageInterfacesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ManageInterfacesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageInterfacesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
