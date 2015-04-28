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

 
define(function(require){
    'use strict';

	var Backbone		= require('backbone');

	var localization	= require('utils/XALangSupport');
	var XAUtil			= require('utils/XAUtils');
	var XAEnums			= require('utils/XAEnums');
    
	var VPasswordChange	= require("models/VXPasswordChange");

	require('backbone-forms.templates');
	require('backbone-forms');

	var UserProfileForm = Backbone.Form.extend(
	/** @lends UserProfileForm */
	{
		_viewName : 'UserProfileForm',
		
    	/**
		* intialize a new UserProfileForm Form View 
		* @constructs
		*/
		initialize: function(options) {
			console.log("initialized a UserProfileForm Form View");
    		Backbone.Form.prototype.initialize.call(this, options);

			_.extend(this, _.pick(options, 'showBasicFields'));
			this.initializeCollection();
			this.bindEvents();
		},
		
		/** all events binding here */
		bindEvents : function(){
			this.on('oldPassword:blur', function(form, fieldEditor){
    			this.evOldPasswordChange(form, fieldEditor);
    		});
		},
		initializeCollection: function(){
		},
		
		/** fields for the form
		*/
		schema :function(){
			var that = this;
			//var plugginAttr = this.getPlugginAttr(true);
		},

		/** on render callback */
		render: function(options) {
			var that = this;
			 Backbone.Form.prototype.render.call(this, options);
			this.initializePlugins();
			this.showCustomFields();
			if(!this.model.isNew()){
				if(this.model.has('userRoleList')){
					var roleList = this.model.get('userRoleList');
					if(!_.isUndefined(roleList) && roleList.length > 0){
						if(XAEnums.UserRoles[roleList[0]].value == XAEnums.UserRoles.ROLE_USER.value)
							this.fields.userRoleList.setValue(XAEnums.UserRoles.ROLE_USER.value);
						else if(XAEnums.UserRoles[roleList[0]].value == XAEnums.UserRoles.ROLE_KEY_ADMIN.value)
							this.fields.userRoleList.setValue(XAEnums.UserRoles.ROLE_KEY_ADMIN.value);
						else
							this.fields.userRoleList.setValue(XAEnums.UserRoles.ROLE_SYS_ADMIN.value);
					}
				}
				if(!_.isUndefined(this.model.get('userSource')) && this.model.get('userSource') == XAEnums.UserSource.XA_USER.value){
					this.fields.firstName.editor.$el.attr('disabled',true);
					this.fields.lastName.editor.$el.attr('disabled',true);
					this.fields.emailAddress.editor.$el.attr('disabled',true);
					
				}
			}
		},
		showCustomFields : function(){
			if(!this.showBasicFields){
				this.fields.firstName.$el.hide();
				this.fields.lastName.$el.hide();
				this.fields.emailAddress.$el.hide();
				this.fields.userRoleList.$el.hide();
				this.fields.firstName.editor.validators.pop();
//				this.fields.lastName.editor.validators.pop();
				this.fields.lastName.editor.validators = [];
			//	this.fields.emailAddress.editor.validators.pop();
				
				this.fields.oldPassword.$el.show();
				this.fields.newPassword.$el.show();
				this.fields.reEnterPassword.$el.show();
				this.fields.oldPassword.editor.validators = ['required'];
				this.fields.newPassword.editor.validators = ['required',{type : 'regexp' ,regexp :/^.*(?=.{8,256})(?=.*\d)(?=.*[a-zA-Z]).*$/, message : localization.tt('validationMessages.newPasswordError')}];
				this.fields.reEnterPassword.editor.validators = ['required',
				                                                 {type : 'regexp' ,regexp :/^.*(?=.{8,256})(?=.*\d)(?=.*[a-zA-Z]).*$/, message : localization.tt('validationMessages.newPasswordError')},
				                                                 { type: 'match', field: 'newPassword', message: 'Passwords must match!' }];
			}
		},
		formValidation : function(){
		},
		
		afterCommit : function(){
//			this.model.unset('userRoleList');
			if(this.model.get('userRoleList') == XAEnums.UserRoles.ROLE_SYS_ADMIN.value){
				this.model.set('userRoleList',["ROLE_SYS_ADMIN"]);
			}else if(this.model.get('userRoleList') == XAEnums.UserRoles.ROLE_USER.value){
				this.model.set('userRoleList',["ROLE_USER"]);
			}else if(this.model.get('userRoleList') == XAEnums.UserRoles.ROLE_KEY_ADMIN.value){
				this.model.set('userRoleList',["ROLE_KEY_ADMIN"]);
			}
		},
		/** all post render plugin initialization */
		initializePlugins: function(){
		},
		evOldPasswordChange : function(form , fieldEditor){
			var that = this;
			var vPasswordChange = new VPasswordChange();
			vPasswordChange.set({
				loginId : this.model.get('id'),
				emailAddress :this.model.get('emailAddress'), 
				oldPassword : that.fields.oldPassword.getValue()
				//updPassword : this.model.get('newPassword'),
			});
			this.model.changePassword(this.model.get('id'),vPasswordChange,{
				wait: true,
				success: function () {
					XAUtil.notifySuccess('Success', "User profile updated successfully !!");
					console.log("success");
				},
				error: function (msResponse, options) {
					console.log("error occured during updated user profile: "+localization.tt(msResponse.responseJSON.msgDesc));
					if(!localization.tt(msResponse.responseJSON.msgDesc) == "Invalid new password"){
						that.fields.oldPassword.setError(localization.tt('validationMessages.oldPasswordError'));
						XAUtil.notifyInfo('',localization.tt('msg.myProfileError'));
					}
				}	
			});
		},

	});

	return UserProfileForm;
});
