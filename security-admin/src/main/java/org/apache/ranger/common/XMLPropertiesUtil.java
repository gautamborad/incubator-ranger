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

package org.apache.ranger.common;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Properties;

import org.apache.hadoop.conf.Configuration;
import org.apache.log4j.Logger;
import org.springframework.util.DefaultPropertiesPersister;

public class XMLPropertiesUtil extends DefaultPropertiesPersister {
	private static Logger logger = Logger.getLogger(XMLPropertiesUtil.class);
//	protected List<String> xmlLocations = new ArrayList<String>();
//
//	public List<String> getXmlLocations() {
//		return xmlLocations;
//	}
//
//	public void setXmlLocations(List<String> xmlLocations) {
//		this.xmlLocations = xmlLocations;
//	}

	public XMLPropertiesUtil() {
	}

	public Map<String, String> processProperties(InputStream inputStream) {
		Configuration configuration = getRANGERConf(inputStream);
		Map<String, String> propertiesMap = new HashMap<String, String>();
		for (Iterator<Entry<String, String>> configurationIterator = configuration
				.iterator(); configurationIterator.hasNext();) {
			Map.Entry<String, String> configurationEntry = (Map.Entry<String, String>) configurationIterator
					.next();
			propertiesMap.put(configurationEntry.getKey().trim(),
					configurationEntry.getValue().trim());
		}

		return propertiesMap;
	}

	public static Configuration getRANGERConf(InputStream inputStream) {
		return getConfiguration(false, inputStream);
	}

	static Configuration getConfiguration(boolean loadHadoopDefaults,
			InputStream inputStream) {
		Configuration conf = new Configuration(loadHadoopDefaults);
		if (inputStream != null) {
			try {
				conf.addResource(inputStream);

			} catch (Exception ex) {
				logger.error(ex.getMessage());
				ex.printStackTrace();
				throw new RuntimeException(ex);
			}
		} else {
			conf.addResource(inputStream);
		}
		return conf;
	}

	@Override
	public void loadFromXml(Properties properties, InputStream inputStream)
			throws IOException {
		properties.putAll(processProperties(inputStream));
	}

}
