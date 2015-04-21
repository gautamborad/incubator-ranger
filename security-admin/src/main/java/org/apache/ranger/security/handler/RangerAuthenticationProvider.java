package org.apache.ranger.security.handler;

import javax.naming.ldap.InitialLdapContext;

import org.apache.ranger.common.PropertiesUtil;
import org.springframework.ldap.core.DirContextOperations;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.ldap.DefaultSpringSecurityContextSource;
import org.springframework.security.ldap.authentication.LdapAuthenticationProvider;
import org.springframework.security.ldap.authentication.LdapAuthenticator;
import org.springframework.security.ldap.authentication.ad.ActiveDirectoryLdapAuthenticationProvider;
import org.springframework.security.ldap.userdetails.DefaultLdapAuthoritiesPopulator;
import org.springframework.security.ldap.userdetails.LdapAuthoritiesPopulator;

public class RangerAuthenticationProvider implements AuthenticationProvider {

	private String rangerAuthenticationMethod;

	private LdapAuthenticator authenticator;

	public RangerAuthenticationProvider() {

	}

	public Authentication initializeAuthenticationHandler(Authentication authentication) {
		if (rangerAuthenticationMethod.equalsIgnoreCase("LDAP")) {
			return getLdapAuthentication(authentication);
		}
		
		return null;

	}

	private Authentication getLdapAuthentication(Authentication authentication){
		boolean isUserLdapAuthenticated = false;
		
		
		LdapAuthenticationProvider ldapAuthenticationProvider = new LdapAuthenticationProvider(authenticator);
		
//		ldapAuthenticationProvider
		
		DirContextOperations authAdapter = authenticator.authenticate(authentication);
		
		String rangerLdapURL 				= PropertiesUtil.getProperty("ranger.ldap.url","");
		String rangerLdapUserDNPattern 		= PropertiesUtil.getProperty("ranger.ldap.user.dnpattern","");
		String rangerLdapGroupSearchBase 	= PropertiesUtil.getProperty("ranger.ldap.group.searchbase","");
		String rangerLdapGroupSearchFilter	= PropertiesUtil.getProperty("ranger.ldap.group.searchfilter","");
		String rangerLdapGroupRoleAttribute = PropertiesUtil.getProperty("ranger.ldap.group.roleattribute","");
		String rangerLdapDefaultRole 		= PropertiesUtil.getProperty("ranger.ldap.default.role","");
		
		
		// Grab the username and password out of the authentication object.
		String principal =  authentication.getName();
		String password = "";
		if (authentication.getCredentials() != null) {
			password = authentication.getCredentials().toString();
		}
		
		DefaultSpringSecurityContextSource contextSource = new DefaultSpringSecurityContextSource(rangerLdapURL);
	    contextSource.setUserDn(rangerLdapUserDNPattern);
	    contextSource.setPassword("");
	    DefaultLdapAuthoritiesPopulator defaultLdapAuthoritiesPopulator = new DefaultLdapAuthoritiesPopulator(contextSource, rangerLdapGroupSearchBase);
	    defaultLdapAuthoritiesPopulator.setGroupRoleAttribute(rangerLdapGroupRoleAttribute);
	    defaultLdapAuthoritiesPopulator.setGroupSearchFilter(rangerLdapGroupSearchFilter);
	    defaultLdapAuthoritiesPopulator.setDefaultRole(rangerLdapDefaultRole);
	    defaultLdapAuthoritiesPopulator.setIgnorePartialResultException(true);
	    
		return null;
		
	}
	
	
	public ActiveDirectoryLdapAuthenticationProvider getAdLdapAuthentication(Authentication authentication) {
		ActiveDirectoryLdapAuthenticationProvider provider = new ActiveDirectoryLdapAuthenticationProvider("company.tld", "ldap://LDAP_URL:389");
	    provider.setConvertSubErrorCodesToExceptions(true);
	    provider.setUseAuthenticationRequestCredentials(true);

//	    provider.setAuthoritiesMapper(myAuthoritiesMapper()); // see http://comdynamics.net/blog/544/spring-security-3-integration-with-active-directory-ldap/

	    provider.setUseAuthenticationRequestCredentials(true);
	    
	    
	    new ActiveDirectoryLdapAuthenticationProvider("my.domain", "ldap://LDAP_ID:389/OU=A_GROUP,DC=domain,DC=tld");
        provider.setConvertSubErrorCodesToExceptions(true);
        provider.setUseAuthenticationRequestCredentials(true);
        provider.setUseAuthenticationRequestCredentials(true);

//	    return provider;
		
		return null;
	}

	@Override
	public Authentication authenticate(Authentication authentication)
			throws AuthenticationException {
		
		String rangerLdapURL 				= PropertiesUtil.getProperty("ranger.ldap.url","");
		String rangerLdapUserDNPattern 		= PropertiesUtil.getProperty("ranger.ldap.user.dnpattern","");
		String rangerLdapGroupSearchBase 	= PropertiesUtil.getProperty("ranger.ldap.group.searchbase","");
		String rangerLdapGroupSearchFilter	= PropertiesUtil.getProperty("ranger.ldap.group.searchfilter","");
		String rangerLdapGroupRoleAttribute = PropertiesUtil.getProperty("ranger.ldap.group.roleattribute","");
		String rangerLdapDefaultRole 		= PropertiesUtil.getProperty("ranger.ldap.default.role","");

		
//		WebSecurityConfigurerAdapter		
//		if(rangerAuthenticationMethod.equalsIgnoreCase("LDAP")) {
//			authentication.ldapAuthentication()
//            .userSearchBase("")
//            .userSearchFilter("(&(cn={0}))").contextSource()
//            .managerDn("<username>")
//            .managerPassword("<password>")
//            .url("ldap://<url>");
//		}
		
		return null;

//		return initializeAuthenticationHandler(authentication);
	}

	@Override
	public boolean supports(Class<?> authentication) {
		return authentication.equals(UsernamePasswordAuthenticationToken.class);
	}

	public String getRangerAuthenticationMethod() {
		return rangerAuthenticationMethod;
	}

	public void setRangerAuthenticationMethod(String rangerAuthenticationMethod) {
		this.rangerAuthenticationMethod = rangerAuthenticationMethod;
	}

	public LdapAuthenticator getAuthenticator() {
		return authenticator;
	}

	public void setAuthenticator(LdapAuthenticator authenticator) {
		this.authenticator = authenticator;
	}

}