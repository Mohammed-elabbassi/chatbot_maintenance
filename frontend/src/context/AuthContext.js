// src/context/AuthContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

// Mapping: company name → tenant DB name
const COMPANY_TENANT_MAP = {
  'jln':                    'v3_tenant_jln',
  'khouribga':              'v3_tenant_jln',
  'safi':                   'v3_tenant_Site_Safi',
  'site safi':              'v3_tenant_Site_Safi',
  'ocp safi':               'v3_tenant_Site_Safi',
  'cmcp':                   'v3_tenant_cmcp_ip',
  'cmcp ip':                'v3_tenant_cmcp_ip',
  'casablanca chimie':      'v3_tenant_cmcp_ip',
  'cobomi':                 'v3_tenant_cobomi',
  'jfc4':                   'v3_tenant_jfc4',
  'jorf lasfar':            'v3_tenant_jfc4',
  'jorf':                   'v3_tenant_jfc4',
  'nomac':                  'v3_tenant_nomac',
  'ntn':                    'v3_tenant_ntn',
  'onee':                   'v3_tenant_onee',
  'bouskoura':              'v3_tenant_lafarge_holcim_bouskoura',
  'lafarge':                'v3_tenant_lafarge_holcim_bouskoura',
  'lafarge holcim':         'v3_tenant_lafarge_holcim_bouskoura',
};

const ALL_TENANTS = [
  { id: 'v3_tenant_jln',                     label: 'v3_tenant_jln',                    shortName: 'JLN' },
  { id: 'v3_tenant_Site_Safi',               label: 'v3_tenant_Site_Safi',              shortName: 'Site Safi' },
  { id: 'v3_tenant_cmcp_ip',                 label: 'v3_tenant_cmcp_ip',               shortName: 'CMCP IP' },
  { id: 'v3_tenant_cobomi',                  label: 'v3_tenant_cobomi',                shortName: 'COBOMI' },
  { id: 'v3_tenant_jfc4',                    label: 'v3_tenant_jfc4',                  shortName: 'JFC4' },
  { id: 'v3_tenant_nomac',                   label: 'v3_tenant_nomac',                 shortName: 'NOMAC' },
  { id: 'v3_tenant_ntn',                     label: 'v3_tenant_ntn',                   shortName: 'NTN' },
  { id: 'v3_tenant_onee',                    label: 'v3_tenant_onee',                  shortName: 'ONEE' },
  { id: 'v3_tenant_lafarge_holcim_bouskoura',label: 'v3_tenant_lafarge_holcim_bouskoura', shortName: 'Lafarge Holcim' },
];

function getAuthorizedTenants(companiesString) {
  if (!companiesString) return [];
  const companies = companiesString.split(',').map(c => c.trim().toLowerCase());
  const authorized = new Set();
  companies.forEach(company => {
    const tenantId = COMPANY_TENANT_MAP[company];
    if (tenantId) authorized.add(tenantId);
    // Also match partial
    Object.entries(COMPANY_TENANT_MAP).forEach(([key, val]) => {
      if (company.includes(key) || key.includes(company)) authorized.add(val);
    });
  });
  return ALL_TENANTS.filter(t => authorized.has(t.id));
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('ichat_user');
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    const authorizedTenants = getAuthorizedTenants(userData.entreprises || '');
    const enriched = {
      ...userData,
      authorizedTenants,
      allTenants: ALL_TENANTS,
    };
    setUser(enriched);
    localStorage.setItem('ichat_user', JSON.stringify(enriched));
    return enriched;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('ichat_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, ALL_TENANTS }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
export { ALL_TENANTS };
