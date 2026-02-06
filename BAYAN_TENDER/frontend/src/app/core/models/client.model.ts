export interface Client {
  id: number;
  name: string;
  nameAr?: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
  crNumber?: string; // Commercial Registration Number
  vatNumber?: string;
  contactPerson?: string;
  contactEmail?: string;
  contactPhone?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  tendersCount?: number;
  totalContractValue?: number;
}

export interface CreateClientDto {
  name: string;
  nameAr?: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
  crNumber?: string;
  vatNumber?: string;
  contactPerson?: string;
  contactEmail?: string;
  contactPhone?: string;
}

export interface UpdateClientDto extends Partial<CreateClientDto> {
  isActive?: boolean;
}
