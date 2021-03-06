/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/**
 *
 */
package org.apache.ranger.security.web.authentication;

import java.io.IOException;
import java.util.Date;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import org.apache.log4j.Logger;
import org.apache.ranger.common.JSONUtil;
import org.apache.ranger.common.PropertiesUtil;
import org.apache.ranger.common.RangerConfigUtil;
import org.apache.ranger.view.VXResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.LoginUrlAuthenticationEntryPoint;

/**
 * 
 *
 */
public class RangerAuthenticationEntryPoint extends
		LoginUrlAuthenticationEntryPoint {
	public static final int SC_AUTHENTICATION_TIMEOUT = 419;

	static Logger logger = Logger.getLogger(RangerAuthenticationEntryPoint.class);
	static int ajaxReturnCode = -1;

	@Autowired
	RangerConfigUtil configUtil;

	@Autowired
	JSONUtil jsonUtil;

	public RangerAuthenticationEntryPoint() {
		super();
		if (logger.isDebugEnabled()) {
			logger.debug("AjaxAwareAuthenticationEntryPoint(): constructor");
		}

		if (ajaxReturnCode < 0) {
		ajaxReturnCode = PropertiesUtil.getIntProperty("ranger.ajax.auth.required.code", 401);
		}
	}

	@Override
	public void commence(HttpServletRequest request,
			HttpServletResponse response, AuthenticationException authException)
			throws IOException, ServletException {
		HttpSession httpSession = request.getSession();
		String ajaxRequestHeader = request.getHeader("X-Requested-With");
		if (logger.isDebugEnabled()) {
			logger.debug("commence() X-Requested-With=" + ajaxRequestHeader);
		}

		String requestURL = (request.getRequestURL() != null) ? request.getRequestURL().toString() : "";
		String servletPath = PropertiesUtil.getProperty("ranger.servlet.mapping.url.pattern", "service");
		String reqServletPath = configUtil.getWebAppRootURL() + "/" + servletPath;

		response.setContentType("application/json;charset=UTF-8");
		response.setHeader("Cache-Control", "no-cache");
		// getting the current date in milliseconds
		Date curentDate = new Date();
		Long currentDateInMillis = (long) (((((curentDate.getHours() * 60) + curentDate
				.getMinutes()) * 60) + curentDate.getSeconds()) * 1000);
		// checking session timeout occurence
		if (httpSession.getMaxInactiveInterval() * 60000 >= (currentDateInMillis - httpSession
				.getLastAccessedTime())) {
			ajaxRequestHeader = null;
			VXResponse vXResponse = new VXResponse();

			vXResponse.setStatusCode(SC_AUTHENTICATION_TIMEOUT);
			vXResponse.setMsgDesc("Session Timeout");

			response.setStatus(SC_AUTHENTICATION_TIMEOUT);
			response.getWriter()
					.write(jsonUtil.writeObjectAsString(vXResponse));

		} else {
			try {

				VXResponse vXResponse = new VXResponse();

				vXResponse.setStatusCode(HttpServletResponse.SC_UNAUTHORIZED);
				vXResponse.setMsgDesc("Authentication Failed");

				response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
				response.getWriter().write(
						jsonUtil.writeObjectAsString(vXResponse));
			} catch (IOException e) {
				logger.info("Error while writing JSON in HttpServletResponse");
			}
		}

		if (ajaxRequestHeader != null
				&& ajaxRequestHeader.equalsIgnoreCase("XMLHttpRequest")) {
			if (logger.isDebugEnabled()) {
				logger.debug("commence() AJAX request. Authentication required. Returning "
						+ ajaxReturnCode + ". URL=" + request.getRequestURI());
			}
			response.sendError(ajaxReturnCode, "");
		} else if (!(requestURL.startsWith(reqServletPath))) {
			super.commence(request, response, authException);
		}

	}

}
